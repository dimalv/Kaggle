# coding: utf-8
'''
 # **An Interactive Data Science Tutorial**


 *[Based on the Titanic competition on Kaggle]
 (https://www.kaggle.com/c/titanic)*

 *by Helge Bjorland & Stian Eide*

 *January 2017*

 ---

 ## Content

  1. Business Understanding (5 min)
      * Objective
      * Description
  2. Data Understanding (15 min)
     * Import Libraries
     * Load data
     * Statistical summaries and visualisations
     * Excersises
  3. Data Preparation (5 min)
     * Missing values imputation
     * Feature Engineering
  4. Modeling (5 min)
      * Build the model
  5. Evaluation (25 min)
      * Model performance
      * Feature importance
      * Who gets the best performing model?
  6. Deployment  (5 min)
      * Submit result to Kaggle leaderboard

 [*Adopted from Cross Industry Standard Process for Data Mining (CRISP-DM)*]
 (http://www.sv-europe.com/crisp-dm-methodology/)

 ![CripsDM](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/
 CRISP-DM_Process_Diagram.png/220px-CRISP-DM_Process_Diagram.png "Process
 diagram showing the relationship between the different phases of CRISP-DM")

 # 1. Business Understanding

 ## 1.1 Objective
 Predict survival on the Titanic

 ## 1.2 Description
 The sinking of the RMS Titanic is one of the most infamous shipwrecks in
 history.  On April 15, 1912, during her maiden voyage, the Titanic sank after
 colliding with an iceberg, killing 1502 out of 2224 passengers and crew.
 This sensational tragedy shocked the international community and led to better
 safety regulations for ships.

 One of the reasons that the shipwreck led to such loss of life was that there
 were not enough lifeboats for the passengers and crew. Although there was some
 element of luck involved in surviving the sinking, some groups of people were
 more likely to survive than others, such as women, children, and the
 upper-class.

 In this challenge, we ask you to complete the analysis of what sorts of people
 were likely to survive. In particular, we ask you to apply the tools of
 machine learning to predict which passengers survived the tragedy.

 **Before going further, what do you think is the most important reasons
 passangers survived the Titanic sinking?**

 [Description from Kaggle](https://www.kaggle.com/c/titanic)
'''


# # 2. Data Understanding
#
# %% 2.1 Import Libraries

# Ignore warnings
import warnings

# Handle table-like data and matrices
import numpy as np
import pandas as pd

# Modelling Algorithms
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC, LinearSVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network.multilayer_perceptron import MLPClassifier

# Modelling Helpers
from sklearn.preprocessing import Imputer, Normalizer, scale
from sklearn.cross_validation import StratifiedKFold
from sklearn.feature_selection import RFECV
from sklearn.model_selection import train_test_split

# Visualisation
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

# %% Config

warnings.filterwarnings('ignore')

# Configure visualisations
# get_ipython().magic(u'matplotlib inline')
# get_ipython().magic(u'matplotlib')
mpl.style.use('ggplot')
sns.set_style('white')
# mpl.rcParams['figure.figsize'] = (14, 6)

FLAGS= {'Analyse': False,
        'Fitting': True,
        'Deploy': False}

# %% 2.2 Setup helper Functions


def plot_histograms(df, variables, n_rows, n_cols):
    fig = plt.figure(figsize=(16, 12))
    for i, var_name in enumerate(variables):
        ax = fig.add_subplot(n_rows, n_cols, i+1)
        df[var_name].hist(bins=10, ax=ax)
        ax.set_title('Skew: ' + str(round(float(df[var_name].skew()),)))
        # + ' ' + var_name) #var_name+" Distribution")
        ax.set_xticklabels([], visible=False)
        ax.set_yticklabels([], visible=False)
    fig.tight_layout()  # Improves appearance a bit.
    plt.show()


def plot_distribution(df, var, target, **kwargs):
    row = kwargs.get('row', None)
    col = kwargs.get('col', None)
    facet = sns.FacetGrid(df, hue=target, aspect=4, row=row, col=col)
    facet.map(sns.kdeplot, var, shade=True)
    facet.set(xlim=(0, df[var].max()))
    facet.add_legend()


def plot_categories(df, cat, target, **kwargs):
    row = kwargs.get('row', None)
    col = kwargs.get('col', None)
    facet = sns.FacetGrid(df, row=row, col=col)
    facet.map(sns.barplot, cat, target)
    facet.add_legend()


def plot_correlation_map(df):
    corr = titanic.corr()
    _, ax = plt.subplots(figsize=(12, 10))
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    _ = sns.heatmap(
        corr,
        cmap=cmap,
        square=True,
        cbar_kws={'shrink': .9},
        ax=ax,
        annot=True,
        annot_kws={'fontsize': 12}
        )


def describe_more(df):
    var = []
    lv = []
    t = []
    for x in df:
        var.append(x)
        lv.append(len(pd.value_counts(df[x])))
        t.append(df[x].dtypes)
    levels = pd.DataFrame({'Variable': var, 'Levels': lv, 'Datatype': t})
    levels.sort_values(by='Levels', inplace=True)
    return levels


def plot_variable_importance(X, y):
    '''
    Train a cllassification tree to estimate the importance of eanch feature
    '''
    tree = DecisionTreeClassifier(random_state=99)
    tree.fit(X, y)
    plot_model_var_imp(tree, X, y)


def plot_model_var_imp(model, X, y):
    imp = pd.DataFrame(
        model.feature_importances_,
        columns=['Importance'],
        index=X.columns
        )
    imp = imp.sort_values(['Importance'], ascending=True)
    imp[:10].plot(kind='barh')
    print(model.score(X, y))


# %% 2.3 Load data
train = pd.read_csv("./train.csv")
test = pd.read_csv("./test.csv")

full = train.append(test, ignore_index=True)
titanic = full[:891]

del train, test

print('Datasets:', 'full:', full.shape, 'titanic:', titanic.shape)

# %% 2.4 Data analysis
# **VARIABLE DESCRIPTIONS:**
#
# We've got a sense of our variables, their class type, and the first few observations of each. We know we're working with 1309 observations of 12 variables. To make things a bit more explicit since a couple of the variable names aren't 100% illuminating, here's what we've got to deal with:
#
#
# **Variable Description**
#
#  - Survived: Survived (1) or died (0)
#  - Pclass: Passenger's class
#  - Name: Passenger's name
#  - Sex: Passenger's sex
#  - Age: Passenger's age
#  - SibSp: Number of siblings/spouses aboard
#  - Parch: Number of parents/children aboard
#  - Ticket: Ticket number
#  - Fare: Fare
#  - Cabin: Cabin
#  - Embarked: Port of embarkation
#
# [More information on the Kaggle site](https://www.kaggle.com/c/titanic/data)

if FLAGS['Analyse']:
    # key information
    titanic.describe()

    # A heat map of correlation
    plot_correlation_map(titanic)
    plt.title('Features correlation')

    # Distributions of Age of passangers who survived or did not survive
    plot_distribution(titanic, var = 'Age', target = 'Survived', row = 'Sex')

    # Distributions of Fare of passangers who survived or did not survive
    plot_distribution(titanic, var = 'Fare', target = 'Survived', row = 'Sex')

    # Plot survival rate by Embarked (Categorical)
    plot_categories(titanic, cat = 'Embarked', target = 'Survived')

    # Survival vs Sex, Pclass, SibSp, and Parch
    #mpl.rcParams['figure.figsize'] = (14, 6)
    fig = plt.figure()
    plt.subplot(221)
    sns.barplot(titanic['Sex'], titanic['Survived'])
    plt.subplot(222)
    sns.barplot(titanic['Pclass'], titanic['Survived'])
    plt.subplot(223)
    sns.barplot(titanic['SibSp'], titanic['Survived'])
    plt.subplot(224)
    sns.barplot(titanic['Parch'], titanic['Survived'])
    # plot_categories(df=titanic, cat='Sex', target='Survived')

# %% 3. Data Preparation

# %% 3.1 1-hot encoding for categorical variables

# Transform Sex into binary values 0 and 1
sex = pd.Series(np.where(full.Sex == 'male', 1, 0), name='Sex')

# Create a new variable for every unique value of Embarked
embarked = pd.get_dummies(full.Embarked, prefix='Embarked')

# Create a new variable for every unique value of Embarked
pclass = pd.get_dummies(full.Pclass, prefix='Pclass')


# %% 3.2 Fill missing values in variables

# Create dataset
imputed = pd.DataFrame()

# Fill missing values of Age with the average of Age (mean)
imputed['Age'] = full.Age.fillna(full.Age.mean())

# Fill missing values of Fare with the average of Fare (mean)
imputed['Fare'] = full.Fare.fillna(full.Fare.mean())

# %% 3.3 Feature Engineering
# Credit: http://ahmedbesbes.com/
#           how-to-score-08134-in-titanic-kaggle-challenge.html

# %% 3.3.1 Extract titles from passenger names
# Titles reflect social status and may predict survival probability

title = pd.DataFrame()
# we extract the title from each name
title['Title'] = full['Name'].map(
        lambda name: name.split(',')[1].split('.')[0].strip())

# a map of more aggregated titles
Title_Dictionary = {
    "Capt":       "Officer",
    "Col":        "Officer",
    "Major":      "Officer",
    "Jonkheer":   "Royalty",
    "Don":        "Royalty",
    "Sir":        "Royalty",
    "Dr":         "Officer",
    "Rev":        "Officer",
    "the Countess": "Royalty",
    "Dona":       "Royalty",
    "Mme":        "Mrs",
    "Mlle":       "Miss",
    "Ms":         "Mrs",
    "Mr":         "Mr",
    "Mrs":        "Mrs",
    "Miss":       "Miss",
    "Master":     "Master",
    "Lady":       "Royalty"
   }

# we map each title
title['Title'] = title.Title.map(Title_Dictionary)
title = pd.get_dummies(title.Title)

# %% 3.3.2 Extract Cabin category information from the Cabin number

cabin = pd.DataFrame()

# replacing missing cabins with U (for Uknown)
cabin['Cabin'] = full.Cabin.fillna('U')

# mapping each Cabin value with the cabin letter
cabin['Cabin'] = cabin['Cabin'].map(lambda c: c[0])

# dummy encoding ...
cabin = pd.get_dummies(cabin['Cabin'], prefix='Cabin')


# %% 3.3.3 Extract ticket class from ticket number

# a function that extracts each prefix of the ticket,
# returns 'XXX' if no prefix (i.e the ticket is a digit)
def cleanTicket(ticket):
    ticket = ticket.replace('.', '')
    ticket = ticket.replace('/', '')
    ticket = ticket.split()
    ticket = map(lambda t: t.strip(), ticket)
    ticket = list(filter(lambda t: not t.isdigit(), ticket))
    if len(ticket) > 0:
        return ticket[0]
    else:
        return 'XXX'


ticket = pd.DataFrame()

# Extracting dummy variables from tickets:
ticket['Ticket'] = full['Ticket'].map(cleanTicket)
ticket = pd.get_dummies(ticket['Ticket'], prefix='Ticket')

# %% 3.3.4 Create family size and category for family size
# The two variables *Parch* and *SibSp* are used to create the famiy size
# variable

family = pd.DataFrame()

# introducing a new feature: the size of families (including the passenger)
family['FamilySize'] = full['Parch'] + full['SibSp'] + 1

# introducing other features based on the family size
family['Family_Single'] = family['FamilySize'].map(
        lambda s: 1 if s == 1 else 0)
family['Family_Small'] = family['FamilySize'].map(
        lambda s: 1 if 2 <= s <= 4 else 0)
family['Family_Large'] = family['FamilySize'].map(
        lambda s: 1 if 5 <= s else 0)

# %% 3.4 Assemble final datasets for modelling
# Split dataset by rows into test and train in order to have a holdout set to
# do model evaluation on. The dataset is also split by columns in a matrix (X)
# containing the input data and a vector (y) containing the target (or labels).

# %% 3.4.1 Variable selection
# Select which features/variables to inculde in the dataset from the list
# below:
#   imputed, embarked, pclass, sex, family, cabin, ticket, title

#full_X = pd.concat([imputed, embarked, cabin, sex], axis=1)
full_X = pd.concat(
    [imputed, embarked, pclass, sex, family, cabin, ticket, title],
    axis=1
    )

# %% 3.4.2 Create datasets
# Create all datasets that are necessary to train, validate and test models
train_valid_X = full_X[0:891]
train_valid_y = titanic.Survived
test_X = full_X[891:]

# Split to train and validstion
train_X, valid_X, train_y, valid_y = train_test_split(
        train_valid_X, train_valid_y, train_size = .7)

print (full_X.shape, train_X.shape, valid_X.shape, train_y.shape, valid_y.shape, test_X.shape)


# %% 3.4.3 Plot Feature importance
#plot_variable_importance(train_X, train_y)

# %% 4. Modeling
# ## 4.1 Define a model
selected_model = 'NN'

if selected_model == 'RandomForest':
    model = RandomForestClassifier(n_estimators=1000, max_depth=5)
elif selected_model == 'NN':
    model = MLPClassifier((50, 20),
                          solver='lbfgs',
                          learning_rate='adaptive',
                          max_iter=100)
elif selected_model == 'SVM':
    model = SVC()
elif selected_model == 'GradientBoosting':
    model = GradientBoostingClassifier()
elif selected_model == 'KNN':
    model = KNeighborsClassifier(n_neighbors=51)
elif selected_model == 'NaiveBayes':
    model = GaussianNB()
elif selected_model == 'LogisticRegression':
    model = LogisticRegression()
else:
    print('Unsupported Model!')

# ## 4.2 Train the selected model
model.fit(train_X, train_y)


# % 5. Evaluation
if 'results_history' not in locals():
    results_history = np.zeros((0, 2), dtype=float)

train_accuracy = model.score(train_X, train_y)
validation_accuracy = model.score(valid_X, valid_y)
results_history = np.concatenate((results_history, np.array([train_accuracy, validation_accuracy])[None, :]))
print(results_history)

# 5.1 Score the model
print('Train accuracy = %f' % train_accuracy)
print('Validation accuracy = %f' % validation_accuracy)


# =============================================================================
#
#
# # %% 5.2.1 Automagic.
# rfecv = RFECV(estimator=model, step=1, cv=StratifiedKFold(train_y, 2),
#               scoring='accuracy')
# rfecv.fit(train_X, train_y)
#
# print(rfecv.score(train_X, train_y), rfecv.score(valid_X, valid_y))
# print("Optimal number of features: %d" % rfecv.n_features_)
#
# # Plot number of features VS. cross-validation scores
# plt.figure()
# plt.xlabel("Number of features selected")
# plt.ylabel("Cross validation score (nb of correct classifications)")
# plt.plot(range(1, len(rfecv.grid_scores_) + 1), rfecv.grid_scores_)
# plt.show()
#
#
# # %% 5.3 Competition time!
# # It's now time for you to get your hands even dirtier and go at it all by yourself in a `challenge`!
# #
# # 1. Try to the other models in step 4.1 and compare their result
# #     * Do this by uncommenting the code and running the cell you want to try
# # 2. Try adding new features in step 3.4.1
# #     * Do this by adding them in to the function in the feature section.
# #
# #
# # **The winner is the one to get the highest scoring model for the validation set**
#
# # %% 6. Deployment
# #
# # Deployment in this context means publishing the resulting prediction from the model to the Kaggle leaderboard. To do this do the following:
# #
# #  1. select the cell below and run it by pressing the play button.
# #  2. Press the `Publish` button in top right corner.
# #  3. Select `Output` on the notebook menubar
# #  4. Select the result dataset and press `Submit to Competition` button
#
# if FLAGS['Deploy']:
#     test_Y = model.predict(test_X)
#     passenger_id = full[891:].PassengerId
#     test = pd.DataFrame({'PassengerId': passenger_id, 'Survived': test_Y})
#     test.shape
#     test.head()
#     test.to_csv('titanic_pred.csv', index = False)
#
#
# =============================================================================
