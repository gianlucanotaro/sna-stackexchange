import pandas as pd
import numpy as np
import os

currentdirectory = os.getcwd()
data_file = currentdirectory + '/data_output/edge_timezone.csv'
df = pd.read_csv(data_file,
                 sep=',',
                 header=0,
                 index_col=False,
                 mangle_dupe_cols=True,
                 error_bad_lines=True,
                 warn_bad_lines=True,
                 skip_blank_lines=True
                 )


# column in the rating DataFrame
columns = pd.DataFrame(list(df.columns.values))
columns

#  DataFrame  of the data type of each column
data_types = pd.DataFrame(df.dtypes,
                          columns=['Data Type'])
data_types

# the count of missing values in each column
missing_data_counts = pd.DataFrame(df.isnull().sum(),
                                   columns=['Missing Values'])
missing_data_counts

# the count of present values in each column
present_data_counts = pd.DataFrame(df.count(),
                                   columns=['Present Values'])
present_data_counts

# the count of unique values in each column
unique_value_counts = pd.DataFrame(columns=['Unique Values Per Column'])
for v in list(df.columns.values):
    unique_value_counts.loc[v] = [df[v].nunique()]
unique_value_counts


# merge all the DataFrames together by the index
data_quality_report = data_types.join(present_data_counts).join(
    missing_data_counts).join(unique_value_counts)
data_quality_report
print("\nData Quality Report- Timezone Edges")
print("\nDataFrame Shape")
print(df.shape)
print("\nDataFrame Info")
print(df.info())

print(data_quality_report)

# print(tags.describe(include=np.object))

# print(tags.isna)
print("\nDetect missing values")
print(df.isnull)
#tags.dropna(subset=['timeset'], inplace=True)
# drop the columns where at least one element is missing
#tags.dropna(axis='columns', inplace=True)
# Keep only the rows with at least 3 non-NA values
df.dropna(thresh=5, inplace=True)
df

missing_data_counts2 = pd.DataFrame(df.isnull().sum(),
                                    columns=['Missing Values'])
missing_data_counts2

# the count of present values in each column
present_data_counts2 = pd.DataFrame(df.count(),
                                    columns=['Present Values'])
present_data_counts2

unique_value_counts2 = pd.DataFrame(columns=['Unique Values Per Column'])
for v in list(df.columns.values):
    unique_value_counts2.loc[v] = [df[v].nunique()]
unique_value_counts2

data_quality_report2 = data_types.join(present_data_counts2).join(
    missing_data_counts2).join(unique_value_counts2)
data_quality_report2

print("\nData Quality Report - Timezone Edges -after removing missing values")
print(data_quality_report2)
