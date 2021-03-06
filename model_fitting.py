import numpy as np
import pandas as pd
import sklearn as sk
import seaborn as sns
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
from sklearn.feature_selection import f_regression, SelectKBest, f_classif
import matplotlib.pyplot as plt
from scipy import interp

def fit_plot_ROC(features, labels, classifier, cross_val):
	"""
	Purpose: fit a classifier to training data with k-fold cross validation, plot ROC curves for each fold
	Inputs:	features: a pandas dataframe of feature values
			labels: a pandas dataframe of class labels
			classifier: an sklearn classifier e.g., sklearn.linear_model.LogisticRegression()
			cross_val: an sklearn cross-validation object 
	Outputs:	mean_auc: the mean area under the ROC curve for the different folds
				classifier: the fit classifier
				also plots the ROC curves for each fold
	"""
	mean_tpr = 0.0 									#Set mean true positive rate to zero
	mean_fpr = np.linspace(0, 1, 100) 				#Linear spacing for the false positive rate
	for i, (train, test) in enumerate(cross_val): 	#Iterate over the cross validation folds
		#Calculate the probabilities of item identity for this test fold
		probas_ = classifier.fit(features.values[train], labels.values[train]).predict_proba(features.values[test])
		fpr, tpr, thresholds = roc_curve(labels.values[test], probas_[:, 1])	#Compute ROC curve
		mean_tpr += interp(mean_fpr, fpr, tpr) 									#Interpolate curve, add to mean
		mean_tpr[0] = 0.0 														#Set zero index to 0
		roc_auc = auc(fpr, tpr) 												#Get the area under the curve
		plt.plot(fpr, tpr, lw=1, label='ROC fold %d (area = %0.2f)' % (i, roc_auc)) #Plot
	plt.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Chance')	#Plot chance performance
	mean_tpr /= len(cross_val) 												#Calculate the mean true positive rate
	mean_tpr[-1] = 1.0 														#Set the last true positive element to 1
	mean_auc = auc(mean_fpr, mean_tpr) 										#Get the area under the ROC for the mean curve
	plt.plot(mean_fpr, mean_tpr, 'k--', 									#Plot
		label='Mean ROC (area = %0.2f)' % mean_auc, lw=2)
	plt.xlim([-0.05, 1.05])
	plt.ylim([-0.05, 1.05])
	plt.xlabel('False Positive Rate')
	plt.ylabel('True Positive Rate')
	plt.title('Receiver operating characteristic')
	plt.legend(loc="lower right")
	return mean_auc, classifier

def fit_clf(X_train, y_train, X_test, y_test, classifier):
	"""
	Purpose: fit a classifier to training data and get performance on test data
	Inputs:	X_train: training features
			y_train: training labels
			X_test: test features
			y_test: test labels
			classifier: an sklearn classifier object
	Output:	a classifier that has been fit to the training data
	"""
	classifier = classifier.fit(X_train.values, y_train)
	probas_ = classifier.predict_proba(X_test.values)
	fpr, tpr, thresholds = roc_curve(y_test.values, probas_[:, 1])
	roc_auc = auc(fpr, tpr) 												#Get the area under the curve
	plt.plot(fpr, tpr, lw=1, label='Test ROC (area = %0.2f)' % (roc_auc))
	plt.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Chance')	#Plot chance performance
	plt.xlim([-0.05, 1.05])
	plt.ylim([-0.05, 1.05])
	plt.xlabel('False Positive Rate')
	plt.ylabel('True Positive Rate')
	plt.title('Receiver operating characteristic')
	plt.legend(loc="lower right")
	return classifier

def fit_plot_PR(features, labels, classifier, cross_val):
	"""
	Purpose: fit a classifier to training data with k-fold cross validation, plot precision-recall curves for each fold
	Inputs:	features: a pandas dataframe of feature values
			labels: a pandas dataframe of class labels
			classifier: an sklearn classifier e.g., sklearn.linear_model.LogisticRegression()
			cross_val: an sklearn cross-validation object
	Outputs:	classifier: the fit classifier
				also plots the PR curves for each fold
	"""
	mean_precision = 0.0 					#Initialize the mean percision to zero
	mean_recall = np.linspace(0, 1, 100)	#Linear spacing over the recall rate
	for i, (train, test) in enumerate(cross_val):	#Iterate over the cross-vailidation folds
		#Calculate the probabilities of item identity for this test fold
		probas_ = classifier.fit(features.values[train], labels.values[train]).predict_proba(features.values[test])
		precision, recall, _ = precision_recall_curve(labels.values[test], probas_[:, 1])	#Calc P-R curve
		mean_precision += interp(mean_recall, recall[::-1], precision[::-1]) 				#Interpolate for the mean curve
		mean_precision[0] = 1.0 															#Precision at 0 is 1
		precision_score = average_precision_score(labels.values[test], probas_[:, 1], average='micro')	#Get AUC
		plt.plot(recall, precision, lw=1, label='P-R fold %d (area = %0.2f)' % (i, precision_score))	#Plot
	mean_precision /= len(cross_val) 			#Get mean precision
	mean_auc = auc(mean_recall, mean_precision)	#Get mean auc
	plt.plot(mean_recall, mean_precision, 'k--', label='Mean P-R (area = %0.2f)' % mean_auc, lw=2)	#Plot
	plt.legend(loc="upper right")
	plt.xlim([-0.05, 1.05])
	plt.ylim([-0.05, 1.05])
	plt.xlabel('Recall')
	plt.ylabel('Precision')
	plt.title('Precision-Recall Curve')
	return mean_auc, classifier

def get_reliable_features(X, y):
	"""
	Purpose: get the model features related to the labels from highest f-score to lowest f-score
		for classification
	Inputs:	X: dataframe consisting of values for the different features
			y: dataframe consisting of the labels for each feature vector
	Output: a dataframe of f, p-values, and cohen's d values, sorted from highest f-value to lowest
	"""
	f, pval  = f_classif(X, y)										#Do f_classif
	feat_pval = pd.Series(data = pval < (0.05 / len(X.columns)), index = X.columns) #pvals with Bonferroni correction
	feat_f = pd.Series(data = f, index = X.columns)							#f values
	d = []
	for feat in X.columns:
		pooled_var = X.loc[y[y == 0].index][feat].var() + X.loc[y[y == 1].index][feat].var()
		mean_diff = X.loc[y[y == 0].index][feat].mean() - X.loc[y[y == 1].index][feat].mean()
		d.append(np.abs(mean_diff / np.sqrt(pooled_var)))
	cohen_d = pd.Series(data = d, index = X.columns) 
	df = pd.DataFrame()
	df['f_score'] = feat_f
	df['pval'] = feat_pval
	df['cohens_d'] = cohen_d
	df.sort_values('f_score', ascending=False, inplace=True)						#Sort by the f values
	return df

def train_val_auc(X_train, y_train, X_val, y_val, classifier, cross_val):
	"""
	Purpose: get cross-validation performance and validation set performance (area under ROC)
	Inputs:	X_train: training features
			y_train: training labels
			X_val: validation features
			y_val: validation labels
			classifier: an sklearn classifier
			cross_val: an sklearn cross-validation object
	Outputs:	mean_cv_auc: the mean of auc for the cross-validation folds
				std_cv_auc: the standard deviaition of the auc for the cross-validation folds
				train_auc: the auc for the whole training set
				val_auc: the auc for the validation set
	"""
	mean_tpr = 0.0 							#Initialize true positive rate to zero
	mean_fpr = np.linspace(0, 1, 100) 		#Linear spacing of false positive rate from 0 to 1
	cv_aucs = np.zeros(cross_val.n_folds) 	#Array of zeros for the auc for each fold
	for i, (train, test) in enumerate(cross_val): 	#Iterate over the number of cross-validation folds
		#Calculate the probabilities of item identity for this test fold 
		probas_ = classifier.fit(X_train.values[train], y_train.values[train]).predict_proba(X_train.values[test])
		fpr, tpr, _ = roc_curve(y_train.values[test], probas_[:, 1])	#Compute the ROC curve
		mean_tpr += interp(mean_fpr, fpr, tpr)							#Iterpolate and add to the mean curbe
		mean_tpr[0] = 0.0 												#Oth true positive rate is 0
		cv_aucs[i] = auc(fpr, tpr) 										#Add area under curve to auc array
	mean_tpr /= len(cross_val)											#Calc mean true positive rate
	mean_tpr[-1] = 1.0 													#Last true positive rate is 1
	mean_cv_auc = auc(mean_fpr, mean_tpr) 								#Calculate auc of mean curve
	std_cv_auc = np.std(cv_aucs) 										#Calculate standard deviation of aucs
	#Calculate the probabilities of item identity for this training set
	probas_ = classifier.fit(X_train.values, y_train.values).predict_proba(X_train.values)
	fpr, tpr, _ = roc_curve(y_train.values, probas_[:, 1])	#Calculate ROC curve
	train_auc = auc(fpr, tpr)								#Get training auc
	#Calculate probabilities of item identity for the validation set
	probas_ = classifier.predict_proba(X_val.values)
	fpr, tpr, _ = roc_curve(y_val.values, probas_[:, 1])	#Calculate ROC curve
	val_auc = auc(fpr, tpr) 								#Calculate validation auc
	return mean_cv_auc, std_cv_auc, train_auc, val_auc

def add_feature_auc(X_train, y_train, X_val, y_val, classifier, cross_val, n_features):
	"""
	Purpose: add features to model one at a time (best-to-worst) and calculate performance
	Inputs:	X_train: training features
			y_train: training labels
			X_val: validation features
			y_val: validation labels
			classifier: sklearn classifier object
			cross-val: sklearn cross-validation object
			n_features: the maximum number of features to try
	"""
	cv_aucs = pd.Series(index = range(1,n_features+1))	#Empty series for outputs
	cv_stds = pd.Series(index = range(1,n_features+1))
	train_aucs = pd.Series(index = range(1,n_features+1))
	val_aucs = pd.Series(index = range(1,n_features+1))

	for i in xrange(1,n_features+1):										#Iterate over the number of features
		selector = SelectKBest(score_func = f_classif, k=i)					#Initialize selector for the i best features
		selector = selector.fit(X_train, y_train)							#Fit selector
		X_train_new = pd.DataFrame(selector.transform(X_train)) 			#Take i best training features for training
		X_val_new = pd.DataFrame(selector.transform(X_val)) 				#Take i best training features for validation
		mean_cv_auc, std_cv_auc, train_auc, val_auc = train_val_auc(		#Calculate performance
			X_train_new, y_train, X_val_new, y_val, classifier, cross_val)
		cv_aucs[i] = mean_cv_auc											#Store performance metrics
		cv_stds[i] = std_cv_auc
		train_aucs[i] = train_auc
		val_aucs[i] = val_auc

	df = pd.DataFrame(cv_aucs, columns=['cv_auc'])	#Create performance dataframe for output
	df['cv_std'] = cv_stds
	df['train_auc'] = train_aucs
	df['val_auc'] = val_aucs
	return df

def plot_feature_corr(X, f_sz = (11, 9)):
	"""
	Purpose: plot a correlation matrix for the features in X
	Inputs:	X: a pandas dataframe of feature values
			f_sz: a tuple for the figure size
	Output: the correlation matrix of X
	"""
	sns.set(style="white")

	# Compute the correlation matrix
	corr = X.corr()

	# Generate a mask for the upper triangle
	mask = np.zeros_like(corr, dtype=np.bool)
	mask[np.triu_indices_from(mask)] = True
	
	# Set up the matplotlib figure
	f, ax = plt.subplots(figsize= f_sz)
	
	# Generate a custom diverging colormap
	cmap = sns.diverging_palette(220, 10, as_cmap=True)

	# Draw the heatmap with the mask and correct aspect ratio
	sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3,
		square=True, linewidths=.5, cbar_kws={"shrink": .5}, ax=ax)

	return corr

def plot_decision_tree_importance(clf, X):
	"""
	Purpose: plot feature importance for a decision tree
	Inputs: clf: the classifier
			X: feature DataFrame
	Output: a print out and a plot of the feature importance
	"""
	importances = clf.feature_importances_
	indices = np.argsort(importances)[::-1]
	
	# Print the feature ranking
	print("Feature ranking:")
	
	for f in range(X.shape[1]):
		print("%d. feature %s (%f)" % (f + 1, X.columns[indices[f]], importances[indices[f]]))

	# Plot the feature importances of the tree
	plt.figure()
	plt.title("Feature importances")
	plt.bar(range(X.shape[1]), importances[indices],
		color="r", align="center")
	plt.xticks(range(X.shape[1]),
		range(1, X.shape[1] + 1))
	plt.xlim([-1, X.shape[1]])
	plt.show()

def fit_stacked_clf(clfs, clf_2, cv, X_train, y_train):
	"""
	Purpose: fit two stage model to training set
	Inputs: clfs: list of sklearn classifiers for the first stage
			clf_2: single sklearn classifier that will classify based on outputs of first stage
			cv: sklearn cross-validation object
			X_train: pandas dataframe with training features
			y_train: pandas dataframe with training labels
	Outputs: 	clfs: fit versions of the first stage classifiers
				clf_2: fit version of the stage one classifier
	"""
	prob_est = np.zeros((X_train.shape[0], len(clfs)))			#Empty array for stage one probability estimates
	print 'Training classifiers with cross-validation'
	for i, clf in enumerate(clfs): 								#For each classifier
		print i, clf
		for j, (train, val) in enumerate(cv): 					#For each cross-validation fold
			print "Fold", j
			train_feat = X_train.values[train] 					#Training features for this fold
			train_label = y_train.values[train] 				#Training labels for this fold 
			val_feat = X_train.values[val]						#Validation features for this fold
			clf.fit(train_feat, train_label)					#Fit this clf to this training partition
			prob_est[val, i] = clf.predict_proba(val_feat)[:,1]	#Predict class probability for validation fold and store
		clfs[i] = clf.fit(X_train, y_train)						#After cross-validation, re-fit the clf on all training data

	clf_2.fit(prob_est, y_train) 								#Train the the stage two classifier with the probability estimates

	return clfs, clf_2 											#Return the classifiers

def stacked_clf_predict(clfs, clf_2, X_test, y_test, plot = True):
	"""
	Purpose: make predictions with stacked classifier
	Inputs: clfs: list of fit first-stage sklearn classifiers 
			clf_2: single fit second-stage sklearn classifier
			X_test:	test features (pandas dataframe)
			y_test: test labels (pandas dataframe)
			plot: boolean that controls plotting
	Output:	probas_: the probability of class identity
	"""
	test_prob_est = np.zeros((X_test.shape[0], len(clfs)))		#Empty array for probability estimates
	print 'Estimating probabilities for test set'
	for i, clf in enumerate(clfs): 								#For each stage-one classifier
		print 'Classifier', i
		test_prob_est[:, i] = clf.predict_proba(X_test)[:,1]	#Predict the class probability for the test data

	probas_ = clf_2.predict_proba(test_prob_est) 				#Predict the class probability with the second stage classifier
	
	if plot:													#Plot test set ROC curve
		fpr, tpr, thresholds = roc_curve(y_test.values, probas_[:, 1])
		roc_auc = auc(fpr, tpr)
		plt.plot(fpr, tpr, lw=1, label='Test ROC (area = %0.2f)' % (roc_auc))
		plt.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Chance')
		plt.xlim([-0.05, 1.05])
		plt.ylim([-0.05, 1.05])
		plt.xlabel('False Positive Rate')
		plt.ylabel('True Positive Rate')
		plt.title('Receiver operating characteristic')
		plt.legend(loc="lower right")

	return probas_
