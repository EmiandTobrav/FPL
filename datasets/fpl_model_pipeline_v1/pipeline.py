"""Fold-local preprocessing. No global imputed/scaled training table is produced."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import Ridge
from sklearn.utils.validation import check_is_fitted

MISSING='__FPL_MISSING__';UNSEEN='__FPL_UNSEEN__'
MODELS=('ridge','catboost','lightgbm')

class FPLPreprocessor(TransformerMixin,BaseEstimator):
    def __init__(self,numeric_features,categorical_features=(),model='ridge'):
        self.numeric_features=numeric_features
        self.categorical_features=categorical_features
        self.model=model
    def _validate(self,X):
        if not isinstance(X,pd.DataFrame):raise TypeError('X must be a dataframe with named features')
        expected=list(self.numeric_features)+list(self.categorical_features)
        if X.columns.duplicated().any() or set(X.columns)!=set(expected):raise ValueError('Feature columns must match the declared schema exactly; targets/metadata are forbidden')
        for col in self.numeric_features:
            if not pd.api.types.is_numeric_dtype(X[col]):raise TypeError(f'Non-numeric value in {col}')
        numbers=X[list(self.numeric_features)].to_numpy(dtype=float)
        if np.isinf(numbers).any():raise ValueError('Infinite feature value; inspect source rather than silently replacing it')
        return numbers
    def _categories(self,X):
        cats=pd.DataFrame(index=X.index)
        for col in self.categorical_features:
            known=set(self.category_values_[col])
            values=X[col].map(lambda v:MISSING if pd.isna(v) else str(v))
            cats[col]=values.map(lambda v:v if v in known else UNSEEN)
        return cats
    def fit(self,X,y=None):
        if self.model not in MODELS:raise ValueError('Unknown model profile')
        numbers=self._validate(X)
        self.feature_names_in_=np.asarray(list(X.columns),dtype=object)
        self.n_features_in_=len(self.feature_names_in_)
        self.category_values_={}
        for col in self.categorical_features:
            values=sorted({str(v) for v in X[col].dropna()})
            if MISSING in values or UNSEEN in values:raise ValueError('Reserved categorical token in input')
            self.category_values_[col]=[MISSING,UNSEEN]+values
        self.all_missing_numeric_=[col for i,col in enumerate(self.numeric_features) if np.isnan(numbers[:,i]).all()]
        if self.model=='ridge':
            self.imputer_=SimpleImputer(strategy='median',keep_empty_features=True)
            filled=self.imputer_.fit_transform(numbers)
            self.scaler_=StandardScaler().fit(filled)
            if self.categorical_features:
                self.encoder_=OneHotEncoder(categories=[self.category_values_[c] for c in self.categorical_features],handle_unknown='error',sparse_output=False,dtype=float)
                self.encoder_.fit(self._categories(X))
        self.fit_rows_=len(X)
        self.output_features_=list(self.numeric_features)+[col+'__missing' for col in self.numeric_features]
        if self.model=='ridge' and self.categorical_features:
            self.output_features_+=list(self.encoder_.get_feature_names_out(list(self.categorical_features)))
        elif self.model!='ridge':self.output_features_+=list(self.categorical_features)
        return self
    def transform(self,X):
        check_is_fitted(self,'output_features_')
        numbers=self._validate(X)
        missing=np.isnan(numbers).astype(np.int8) # Every numeric feature, including new inference missingness.
        cats=self._categories(X)
        if self.model=='ridge':
            scaled=self.scaler_.transform(self.imputer_.transform(numbers))
            blocks=[scaled,missing]
            if self.categorical_features:blocks.append(self.encoder_.transform(cats))
            return pd.DataFrame(np.hstack(blocks),index=X.index,columns=self.output_features_)
        out=pd.DataFrame(numbers,index=X.index,columns=list(self.numeric_features))
        flags=pd.DataFrame(missing,index=X.index,columns=[c+'__missing' for c in self.numeric_features])
        out=pd.concat([out,flags],axis=1)
        for col in self.categorical_features:
            out[col]=pd.Categorical(cats[col],categories=self.category_values_[col],ordered=False) if self.model=='lightgbm' else cats[col].astype(str)
        return out[self.output_features_]
    def get_feature_names_out(self,input_features=None):
        check_is_fitted(self,'output_features_');return np.asarray(self.output_features_,dtype=object)
    def audit_state(self):
        check_is_fitted(self,'output_features_')
        result={'profile':self.model,'fit_rows':self.fit_rows_,'input_features':list(self.feature_names_in_),'output_features':self.output_features_,'categories':self.category_values_,'all_missing_numeric_features':self.all_missing_numeric_,'missing_indicator_policy':'one explicit flag for every numeric input','numeric_missing_policy':'median fitted on training only; zero if no training evidence, with missing flag' if self.model=='ridge' else 'NaN preserved for native model handling'}
        if self.model=='ridge':
            result.update(imputation_values=dict(zip(self.numeric_features,self.imputer_.statistics_.tolist())),scale_means=dict(zip(self.numeric_features,self.scaler_.mean_.tolist())),scale_factors=dict(zip(self.numeric_features,self.scaler_.scale_.tolist())))
        return result

def make_pipeline(schema,model='ridge',feature_set='baseline',seed=20261013,model_params=None):
    if model not in MODELS:raise ValueError('Unknown model')
    if feature_set not in ['baseline','extended']:raise ValueError('Unknown feature set')
    features=schema[feature_set+'_features']
    categorical=tuple(c for c in features if c in schema['categorical_features'])
    numeric=tuple(c for c in features if c not in categorical)
    prep=FPLPreprocessor(numeric,categorical,model)
    overrides=dict(model_params or {})
    if model=='ridge':
        params={'alpha':10.};params.update(overrides);estimator=Ridge(**params)
    elif model=='catboost':
        from catboost import CatBoostRegressor
        params={'iterations':200,'depth':5,'learning_rate':.05,'loss_function':'RMSE','random_seed':seed,'thread_count':2,'verbose':False,'allow_writing_files':False,'cat_features':categorical}
        params.update(overrides);estimator=CatBoostRegressor(**params)
    else:
        from lightgbm import LGBMRegressor
        params={'n_estimators':200,'max_depth':5,'num_leaves':24,'learning_rate':.05,'objective':'regression','random_state':seed,'n_jobs':2,'verbosity':-1,'zero_as_missing':False}
        params.update(overrides);estimator=LGBMRegressor(**params)
    return Pipeline([('prepare',prep),('model',estimator)])

def fit_fold(rows,schema,forecast_at,model='ridge',feature_set='baseline',horizon=1,window_days=None,model_params=None):
    from loader import select_training_rows,model_view
    training=select_training_rows(rows,forecast_at,horizon,window_days)
    if training.empty:raise ValueError('No causally available training rows at this forecast time')
    view=model_view(training,schema,feature_set,horizon,require_target=True)
    target=view['y'].to_numpy(float)
    if not np.isfinite(target).all():raise ValueError('Training labels must be observed and finite; no target imputation')
    pipeline=make_pipeline(schema,model,feature_set,model_params=model_params)
    pipeline.fit(view['X'],view['y'])
    at=pd.Timestamp(forecast_at)
    feature_state=pipeline.named_steps['prepare'].audit_state()
    audit={'forecast_at':str(at),'horizon':horizon,'model':model,'feature_set':feature_set,'window_days':window_days,'training_rows':len(training),'latest_training_label_available_at':str(training[f'target_h{horizon}_available_at'].max()),'latest_training_forecast_at':str(training.forecast_at.max()),'training_key_sha256':hashlib.sha256(pd.util.hash_pandas_object(training[['season','round','code']],index=False).to_numpy().tobytes()).hexdigest(),'zero_point_training_rows':int((target==0).sum()),'negative_point_training_rows':int((target<0).sum()),'maximum_observed_target':float(target.max()),'labels_clipped_or_resampled':False,'feature_processing':feature_state}
    return pipeline,audit

def predict_rows(pipeline,rows,schema,feature_set='baseline'):
    features=schema[feature_set+'_features']
    predictions=np.asarray(pipeline.predict(rows[features]),dtype=float)
    if predictions.shape!=(len(rows),) or not np.isfinite(predictions).all():raise ValueError('Invalid model predictions')
    out=rows[['season','round','code']].copy();out['predicted_points']=predictions
    return out
