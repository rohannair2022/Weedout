import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler, MinMaxScaler,OneHotEncoder, FunctionTransformer
from statsmodels.stats.outliers_influence import variance_inflation_factor
from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from scipy import stats
from tqdm.notebook import tqdm
from typing import List, Optional, Tuple
import csv

def check_duplicate_columns(file_path: str) -> List[str]:
    """
        The function checks if the dataset has multiple same column names.

        @paramter:

            file_path:
                The path to the csv file 

        @return:

            List[str]:
                A list of all the duplicate column names.

    """
    if file_path.lower().endswith('.csv'):
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            seen = set()
            duplicates = set()
            
            for header in headers:
                if header in seen:
                    duplicates.add(header)
                seen.add(header)
            
            if duplicates:
                return list(duplicates)
            else:
                return []
    else:
        raise Exception('Wrong File Type. Only CSV allowed.')


def initial_check_dt(file_path: str, target_variable: str, columns_to_drop: List[str]) -> Optional[pd.DataFrame]:
    """
        The function initially checks if the file provided is a valid CSV file that can be parsed through. It checks 
        and drops duplicate columns, verifies the target variable, and drops columns with exceedingly high
        null values and untouched columns.

        @parameters:

            file_path : str
                The path to the csv file.

            target_variable : str  
                The target column of your dataset.

            untouched_columns : List[str] 
                The list of columns that are not going to be modified. These 
                would generally be columns that have to do with IDw.
        
        @return:

            Optional[pd.DataFrame] 
                It will return the modified dataframe if the function is successful.

    """
    if file_path.lower().endswith('.csv'):

        try:
            duplicate = check_duplicate_columns(file_path)
            if duplicate:
                raise Exception("Duplicate columns exist in the file:", duplicate)
            df = pd.read_csv(file_path)
        except pd.errors.ParserError:
            raise Exception('File cannot be parsed as a CSV.') from None
        except Exception as e:
            raise Exception(f"An error occurred: {e}") from e
        
        id_drop = [col for col in df.columns if col in columns_to_drop]
        if id_drop:
            df = df.drop(columns=id_drop)
            print(f"Dropped untouched columns: {', '.join(id_drop)}")
            
        drop_columns = []
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            total_values = len(df[col])
            missing_percentage = (missing_count / total_values) * 100

            if missing_percentage > 40:
                drop_columns.append(col)

        print("Dropped columns with high missing data: ", list(drop_columns))
        df = df.drop(columns=drop_columns)
        
        df_columns = df.columns.tolist() 
        keep_indices = []

        for index, col in enumerate(df.columns):
            keep_indices.append(index)

        df = df.iloc[:, keep_indices]
        
        if target_variable in df_columns:
            print(f"The target variable '{target_variable}' is present in the DataFrame.")
        else:
            raise Exception (f"The target variable '{target_variable}' is missing in the DataFrame.")
        
        print("Initial checks and changes made")
        return df
    
    else:
        raise Exception("Oops :( The file is not a CSV file!")

def cross_sectional_imputation(cross_sectional_df: pd.DataFrame) -> pd.DataFrame:
    """
        The function works on imputation for the given cross sectional dataframe. For columns with
        numeric values, the null values of that column are imputed/filled with the mean (average) value 
        of the column. For columns with string values, the null values of that column are imputed/filled
        with the mode (most frequent) value of that column. 

        @parameters:

            cross_sectional_df : pd.DataFrame:
                The dataframe of the cross-sectional dataset with the target column included.
        
        @return:
        
            Optional[pd.DataFrame] 
                It will return the imputed dataframe if the function is successful.

    """
    df = cross_sectional_df.copy()
    
    print("Total Null value counts before imputation: \n",df.isnull().sum())

    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].fillna(df[column].mean())
        else:
            df[column] = df[column].fillna(df[column].mode()[0])
    
    print("\nTotal Null value counts: \n",df.isnull().sum())
    return df

    
def time_series_imputation(time_series_df: pd.DataFrame) -> pd.DataFrame:
    """
        The function works on imputation for the given time series dataframe. For columns with
        numeric values, the null values of that column are imputed/filled through the method of linear 
        interpolation. For columns with string values, the null values of that column are imputed/filled
        with the mode (most frequent) value of that column. 

        @parameters:

            time_series_df : pd.DataFrame:
                The dataframe of the time series dataset with the target column included.
        
        @return:
        
            Optional[pd.DataFrame] 
                It will return the imputed dataframe if the function is successful.
    """
    df = time_series_df.copy()
    
    print("Total Null value counts before imputation: \n",df.isnull().sum())

    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].interpolate(method='linear')
        else:
            df[column] = df[column].fillna(df[column].mode()[0])
        
    print("\nTotal Null value counts: \n",df.isnull().sum())
    print("All Tests Passed")
    return df


def handle_imbalanced_data(df: pd.DataFrame, target_variable: str, strategy = "smote", k_neighbors=2) -> pd.DataFrame:
    """
        The function balances a dataframe defined through a given sampling strategy to be
        ran on a classfication model. 

        @paramters:

            df: pd.DataFrame
                The dataframe for the given dataset.
            
            target_variable: str
                The name of the target column in the dataframe

            stratergy: str: default = SMOTE
                The name of the sampling stratergy:
                    - oversampling 
                    - undersampling 
                    - smote 
            
            k_neighbours: int: default = 2
                The number of neighbours for the Smote Stratergy
        
        @return:

            pd.DataFrame
                The balanced dataframe after following the sampling stratergy.
    
    """

    if strategy == 'oversampling':
        sampler = RandomOverSampler()
    elif strategy == 'undersampling':
        sampler = RandomUnderSampler()
    elif strategy == 'smote':
        sampler = SMOTE(k_neighbors=k_neighbors)
    else:
        raise ValueError("Invalid strategy. Choose from 'oversampling', 'undersampling', or 'smote'.")
    
    print(f'The distribution of the target column prior to sampling: {df[target_variable].value_counts}')
    
    if target_variable not in df.columns:
        raise Exception('Target Column not found in Dataframe')

    X_res, y_res=separate_target_column(df,target_variable)
    X_res, y_res = sampler.fit_resample(X_res, y_res)
    df_balanced = pd.concat([X_res, y_res], axis=1)

    print(f'The distribution of the target column after sampling: {df[target_variable].value_counts}')
    
    return df_balanced

def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
        The function detects outliers outside the range of 2.575 (99% CI) and removes the corresponding
        observations/rows if the outlier is present in more than 10% of the column. 

        @paramters:

            df: pd.DataFrame
                The dataframe for the given dataset.
        
        @return:

            pd.DataFrame
                The balanced dataframe after following the sampling stratergy.

    """
    numerical_features = df.select_dtypes(include=['float64', 'int64']).columns
    df_original = df.copy()

    outlier_counts = pd.Series(0, index=df_original.index)
    threshold = 2.575 # Indicating a 99% CI
    col_count = len(numerical_features)

    for col in numerical_features:
        z_scores = np.abs(stats.zscore(df_original[col]))
        outliers = z_scores > threshold
        outlier_counts += outliers

    # Remove rows with a significant number of outliers.
    df_pre_processed = df_original[outlier_counts < col_count*0.1]

    print(f"\nOriginal data count: {len(df_original)}")
    print(f"After outlier removal data count: {len(df_pre_processed)}")

    return df_pre_processed

def separate_target_column(df: pd.DataFrame, target_variable: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """

        This function separates the given target column from the data frame.    

        @paramters:

            df: pd.DataFrame
                The dataframe for the given dataset that contains the target column as well.
            
            target_variable: str
                The name of the target column in the dataframe.
        
        @return:

            Tuple(pd.DataFrame, pd.DataFrame):
                Tuple[0] : The dataframe with all columns except the target column
                Tuple[1] : The target column dataframe.


    """
    try:
        target = df[target_variable]
        remaining_df = df.drop(columns=[target_variable])
        return remaining_df, target
    except:
        raise Exception('Target Column does not Exist. Please provide the right one.')


def filtered_correlation_matrix(df: pd.DataFrame):
    """
        This function prints the Variance Inflation Factor ( VIF = 1/(1-R^2) ) of each feature column. VIF 
        is a strong indicator of multi-collinearity in our data frame. 

        Note : The user is expected to remove some of the correlated features based on the VIF value.

        @parameter:

            df : pd.DataFrame
                The dataframe provided by user.
        
    """

    numerical_columns = df.select_dtypes(include=['float64', 'int64'])
    non_numerical_columns = df.select_dtypes(exclude=['float64', 'int64']).columns
    print("Before: ", numerical_columns.shape)
    
    vif = pd.DataFrame()
    vif['Feature'] = numerical_columns.columns
    vif["VIF"] = [variance_inflation_factor(numerical_columns.values, i) for i in range(numerical_columns.shape[1])]
    
    print("Initial VIF values: ")
    print(vif.sort_values(by="VIF", ascending=False))


def encoding(features: pd.DataFrame) -> pd.DataFrame:
    """
        The function encodes the object type columns in the given data frame. If the number of
        attributes in a column exceeds more than 3, then the function performs Label Encoding. If it does not, 
        then it performs One Hot Encoding. 

        @parameters:
            features : str
                The data frame consisting of all the features (excluding the target column).
        
        @return:
            pd.DataFrame:
                The dataframe consisting of all the encoded features. 
    """
    for column in features.columns:
        if features[column].dtype == "object":
            if features[column].nunique() > 3:
                encoder = LabelEncoder()
                features[column] = encoder.fit_transform(features[column])
            else:
                encoder = OneHotEncoder(sparse_output=False, drop='first')
                encoded = encoder.fit_transform(features[[column]])
                encoded_features = pd.DataFrame(encoded, columns=encoder.get_feature_names_out([column]), index=features.index)
                features.drop(columns=[column], inplace=True)
                features[encoded_features.columns] = encoded_features

    return features


def feature_scaling(features: pd.DataFrame, unscale_columns: List[str]) -> pd.DataFrame:
    """
        The function scales continuous-numerical values of the dataset. If the values in the column have a normal
        distribution then we do StandardScaling. If it does not, then we do MinMaxScaling
        Note : If the unique value count of the column is greater than 3, only then will the function apply 
        scaling to that column.

        @parameters:

            features:
                The dataframe containing the features to be scaled.
            
            unscale_columns:
                The list of column names that represent the columns that should not be scaled.


        @return:

            pd.DataFrame:   
                The dataframe containing the scaled features.

    
    """
    df = features.copy()
        
    numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns
    non_numerical_columns = df.select_dtypes(exclude=['float64', 'int64']).columns

    def is_normal(column):
        stat, p = stats.shapiro(column)
        alpha = 0.05
        if p > alpha:
            return True
        return False

    
    Minmaxscaler_algorithms = []
    Standardscaler_algorithms = []

    
    for col in numerical_columns:
        if col not in unscale_columns:

            unique_count = df[col].nunique()

            if is_normal(df[col]):
                
                if unique_count > 3: 
                    scaler = StandardScaler()
                    df[col] = scaler.fit_transform(df[[col]])
                    Standardscaler_algorithms.append(col)
            else:
                if unique_count > 3: 
                    scaler = MinMaxScaler()
                    df[col] = scaler.fit_transform(df[[col]])
                    Standardscaler_algorithms.append(col)
            
                        
    print("\nMinmax scaled columns: \n", Minmaxscaler_algorithms)
    print("\nStandardized columns: \n", Standardscaler_algorithms)
    
    df_scaled = pd.concat([df[numerical_columns], df[non_numerical_columns]], axis=1)
    
    df_scaled = df_scaled.reset_index(drop=True)
            
    print("\nScaled data\n")

    return df_scaled

def combine (features: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    """
        The functions combines the features dataframe and target dataframe into one dataframe.

        @paramters:
            features: pd.DataFrame
                The dataframe that consists of all the features
        
            target: pd.DataFrame
                The dataframe that consists of all the targets.
        
        @return:
            
            pd.DataFrame:
                The combined dataframe that consists of both the feature dataframe and the target dataframe.
    
    """
    df = features.copy()
    df[target.name] = target.values
    return df 
    

def display(file_path: str ,df: pd.DataFrame) -> None:
    """
        The function displays the info of the original dataset in the given file path in comparison to
        the preprocessed dataframe.

        @paramters:
            file_path: str 

                The path to the original file.

            df: pd.DataFrame 

                The preproccsed dataframe.

    """
    original_data=pd.read_csv(file_path)
    processed_data=df
    print("\nOriginal Data\n")
    original_data.info()
    print("\nProcessed Data\n")
    processed_data.info()

def preprocess_pipeline(file_path: str, target_column: str, dropped_columns: List[str], type_dataset: int, sampling: int, classfication: int, strategy_sample="SMOTE"):
    total_steps = 11  # Total number of steps in the pipeline
    progress_bar = tqdm(total=total_steps, desc="Pipeline Progress", unit="step")
    
    print("\nInitial Check")
    df = initial_check_dt(file_path, target_column, dropped_columns)
    progress_bar.update(1)
    print("\n-----------------------------Initial check done-----------------------------------------------\n")
    
    print("\nImputation")
    if not type_dataset:
        df = cross_sectional_imputation(df)
        progress_bar.update(1)
        print("\n-----------------------------Cross Sectional Imputation Done-----------------------------------------------\n")
    elif type_dataset == 1:
        df = time_series_imputation(df)
        progress_bar.update(1)
        print("\n-----------------------------Time Series Imputation Done-----------------------------------------------\n")

    if sampling:
        if classfication:
            print("\nHandling Imbalanced Data")
            df = handle_imbalanced_data(df, target_column, strategy_sample)
            progress_bar.update(1)
            print("\n-----------------------------Balanced the data-----------------------------------------------\n")
        else:
           print("\nCant Balance a Dataset for Regression Models")
           print("\n-----------------------------Balanced the data-----------------------------------------------\n")

    print("\nRemoving Outliers")
    df = remove_outliers(df)
    progress_bar.update(1)
    print("\n-----------------------------Removed Outliers-----------------------------------------------\n")
    
    print("\nSeparating Input and Output")
    remaining_df, target = separate_target_column(df, target_column)
    progress_bar.update(1)
    print("\n-----------------------------Separated the input and output-----------------------------------------------\n")
    
    print("\nFinding Correlations")
    filtered_correlation_matrix(remaining_df)
    progress_bar.update(1)
    print("\n-----------------------------Found the correlations-----------------------------------------------\n")
    
    print("\nEncoding Data")
    remaining_df = encoding(remaining_df)
    progress_bar.update(1)
    print("\n-----------------------------Encoded the data-----------------------------------------------\n")
    
    print("\nFeature Scaling")
    preprocessed_df = feature_scaling(remaining_df, dropped_columns)
    progress_bar.update(1)
    print("\n-----------------------------Feature Scaling Done-----------------------------------------------\n")
    
    print("\nCombining Feature and Target")
    combined_df = combine(preprocessed_df,target)
    progress_bar.update(1)
    print("\n-----------------------------Combining Features Done-----------------------------------------------\n")
    
    print("\nDisplaying the results")
    display(file_path,combined_df)
    progress_bar.update(1)
    print("\n-----------------------------Displayed the final results-----------------------------------------------\n")
    
    progress_bar.close()
    return preprocessed_df
