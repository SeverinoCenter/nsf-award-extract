import pandas as pd
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import zipfile
from tldextract import extract

def process_zip_files(base_path, output_path, min_years):
    """
    Processes ZIP files in the given base directory, extracts XML files, and returns a DataFrame
    with information about the extracted files for years > min_years.
    
    Parameters:
        base_path (Path): The base directory containing ZIP files.
        output_path (Path): The directory where files will be temporarily extracted.
        min_years (int): Minimum year to include in the results.
    
    Returns:
        pd.DataFrame: A DataFrame with columns ['file', 'year', 'xmlfiles'].
    """
    base = Path(base_path)
    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)  # Ensure output directory exists
    
    zipfiles = list(base.rglob("*.zip"))  # List all ZIP files in base directory
    details = []
    
    for file in zipfiles:
        print(f"Processing file: {file}")
        file_info = {}
        file_info['file'] = str(file)
        
        # Extract year from filename (assuming the year is in the filename)
        try:
            year = int(file.stem.split(".")[0])  # Adjust split logic based on actual filename format
            file_info['year'] = int(year)
        except ValueError:
            print(f"Could not extract year from filename: {file}")
            continue
        
        # Skip files with years <= min_years
        if year <= min_years:
            continue
        
        # Create a year-specific directory for extraction
        year_dir = output / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract ZIP file contents to the year-specific directory
        try:
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(year_dir)
            file_info['errors']=True
        except Exception as e:
            print(f"Failed to extract {file}: {e}")
            file_info['errors']=False
            continue
        
        # Count the number of XML files in the year-specific directory
        xmlfiles = list(year_dir.rglob("*.xml"))
        file_info['xmlfiles'] = len(xmlfiles)
        
        # Append file info to the details list
        details.append(file_info)
    
    # Convert the details list into a DataFrame
    df = pd.DataFrame(details)
    #sort by year decending
    df.sort_values(by='year', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

    # Helper function to extract the main domain from an email address
    # Helper function to extract the main domain from an email address
def extract_main_domain(email):
    if email and '@' in email:
        domain_parts = email.split('@')[1].split('.')  # Split by '.'
        if len(domain_parts) > 2:
            # Take only the last two parts (e.g., ['ucsd', 'edu'])
            return '.'.join(domain_parts[-2:])
        return '.'.join(domain_parts)  # Return full domain if it's already simple
    return None




def extract_investigators(root, data):
    """
    Extracts investigator data from an XML root and appends it to a list
    with an ordered investigator number (PI#), total investigators count,
    institution domain, collaborative institutions count, 
    and totals for PI's university and others.
    
    Args:
        root: XML root element.
        data: A dictionary containing the AwardID.
    
    Returns:
        A list of dictionaries containing investigator data and collaboration statistics.
    """
    investigators = []
    investigator_elements = root.findall('.//Investigator')
    total_investigators = len(investigator_elements)  # Total investigators count

    # Extract domains and calculate collaboration statistics
    domains = []
    for investigator in investigator_elements:
        email = investigator.findtext('EmailAddress')
        main_domain = extract_main_domain(email)
        domains.append(main_domain)

    unique_domains = set(filter(None, domains))  # Unique institution domains, ignoring None
    pi_domain = domains[0] if domains else None  # Domain of the first investigator (PI)
    
    total_at_pi_university = domains.count(pi_domain)
    total_outside_pi_university = total_investigators - total_at_pi_university

    for idx, investigator in enumerate(investigator_elements, start=1):
        email = investigator.findtext('EmailAddress')
        institution_domain = extract_main_domain(email)
        
        investigator_data = {
            'PI#': idx,  # Ordered investigator number
            'TotalInvestigators': total_investigators,  # Total investigators
            'AwardID': data['AwardID'],  # Add AwardID to each investigator record
            'FirstName': investigator.findtext('FirstName'),
            'LastName': investigator.findtext('LastName'),
            'MiddleInitial': investigator.findtext('PI_MID_INIT'),
            'Suffix': investigator.findtext('PI_SUFX_NAME'),
            'FullName': investigator.findtext('PI_FULL_NAME'),
            'Email': email,
            'InstitutionDomain': institution_domain,  # Extracted main domain
            'NSFID': investigator.findtext('NSF_ID'),
            'StartDate': investigator.findtext('StartDate'),
            'EndDate': investigator.findtext('EndDate'),
            'RoleCode': investigator.findtext('RoleCode'),
            'TotalCollaborativeInstitutions': len(unique_domains),  # Unique institutions
            'TotalAtPIUniversity': total_at_pi_university,  # Count at PI's university
            'TotalOutsidePIUniversity': total_outside_pi_university,  # Count outside PI's university
        }
        investigators.append(investigator_data)
    
    return investigators




def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Common fields (grant data)
        data = {
            'AwardID': root.findtext('.//AwardID'),
            'AwardTitle': root.findtext('.//AwardTitle'),
            'Agency': root.findtext('.//AGENCY'),
            'AwardEffectiveDate': root.findtext('.//AwardEffectiveDate'),
            'AwardExpirationDate': root.findtext('.//AwardExpirationDate'),
            'AwardTotalIntnAmount': root.findtext('.//AwardTotalIntnAmount'),
            'AwardAmount': root.findtext('.//AwardAmount'),
            'AwardInstrument': root.findtext('.//AwardInstrument/Value'),
            'Organization_Code': root.findtext('.//Organization/Code'),
            'Directorate_Abbreviation': root.findtext('.//Directorate/Abbreviation'),
            'Directorate_LongName': root.findtext('.//Directorate/LongName'),
            'Division_Abbreviation': root.findtext('.//Division/Abbreviation'),
            'Division_LongName': root.findtext('.//Division/LongName'),
        }
        investigators = extract_investigators(root, data)

        # Process all investigators
        # investigators = []
        # for investigator in root.findall('.//Investigator'):
        #     investigator_data = {
        #         'AwardID': data['AwardID'],  # Add AwardID to each investigator record
        #         'FirstName': investigator.findtext('FirstName'),
        #         'LastName': investigator.findtext('LastName'),
        #         'MiddleInitial': investigator.findtext('PI_MID_INIT'),
        #         'Suffix': investigator.findtext('PI_SUFX_NAME'),
        #         'FullName': investigator.findtext('PI_FULL_NAME'),
        #         'Email': investigator.findtext('EmailAddress'),
        #         'NSFID': investigator.findtext('NSF_ID'),
        #         'StartDate': investigator.findtext('StartDate'),
        #         'EndDate': investigator.findtext('EndDate'),
        #         'RoleCode': investigator.findtext('RoleCode'),
        #     }
        #     investigators.append(investigator_data)

        # Convert the main data (grant data) into a DataFrame
        df_grant = pd.DataFrame([data])

        # Convert the investigators data into a DataFrame
        df_investigators = pd.DataFrame(investigators)

        # Return two DataFrames: one for the grant and one for the investigators
        return df_grant, df_investigators

    except Exception as e:
        print(f"Error parsing file {file_path}: {str(e)}")
        return None, None

    except ET.ParseError:
        print(f'Error parsing file: {file_path}')
        return None



def collect_data_from_xml_files(root_folder, year):
    """
    Collects data from XML files in the specified year folder.
    
    Parameters:
        root_folder (Path): The root directory containing year folders.
        year (int): The year to process.
    
    Returns:
        pd.DataFrame: A DataFrame with all the collected data.
        list: A list of files that caused errors during parsing.
    """
    data_list = []
    invest_list = []
    error_files = []
    yr_folder = root_folder / str(year)
    xmlfiles = list(yr_folder.rglob("*.xml"))
    
    for filename in xmlfiles:
        try:
            # Parse XML file using the user-defined parse_xml function
            data, invest = parse_xml(filename)

            
            if data is not None and not data.empty:
                data['Year'] = year
                data_list.append(data)
            else:
                error_files.append(str(filename))
            if invest is not None and not invest.empty:
                invest_list.append(invest)
        except Exception as e:
            # Log the file that caused an exception along with the error message
            error_files.append(f"{filename}: {str(e)}")
    
    # Concatenate all collected data into a single DataFrame
    final_data = pd.concat(data_list, ignore_index=True) if data_list else pd.DataFrame()
    final_invest = pd.concat(invest_list, ignore_index=True) if data_list else pd.DataFrame()
    
    return final_data, final_invest, error_files

import pandas as pd
from datetime import datetime
from pathlib import Path

def process_dataframe(df, root_folder, output_csv, output_pkl):
    # Ensure output directories exist
    data_list = []
    invest_list = []
    output_csv.mkdir(parents=True, exist_ok=True)
    output_pkl.mkdir(parents=True, exist_ok=True)

    # Add new columns to the DataFrame if not already present
    for column in ['grant_rows', 'invest_rows', 'xml_errors', 'xml_error_list', 'time_parsed']:
        if column not in df.columns:
            df[column] = None

    # Iterate through each row and process XML files
    for index, row in df.iterrows():
        year = row['year']
        print(f"Processing year: {year}...")

        # Collect data and errors from XML files
        data, invest, error_files = collect_data_from_xml_files(root_folder, year)

        # Update the DataFrame with new information
        df.loc[index, 'grant_rows'] = int(len(data))
        df.loc[index, 'invest_rows'] = int(len(invest))  # Corrected here to use invest instead of data
        df.loc[index, 'xml_errors'] = len(error_files)
        df.loc[index, 'xml_error_list'] = ', '.join(error_files)  # Store error file names as a string
        df.loc[index, 'time_parsed'] = datetime.now()

        # Append data and invest to their respective lists
        data_list.append(data)
        invest_list.append(invest)

        # Save the processed data for the year
        if not data.empty:
            data.to_csv(output_csv / f'{year}.csv', index=False)
            data.to_pickle(output_pkl / f'{year}.pkl')

        if not invest.empty:
            invest.to_csv(output_csv / f'investigator_{year}.csv', index=False)
            invest.to_pickle(output_pkl / f'investigator_{year}.pkl')

    # Combine all grant data and investigator data across all years
    final_data = pd.concat(data_list, ignore_index=True) if data_list else pd.DataFrame()
    final_invest = pd.concat(invest_list, ignore_index=True) if invest_list else pd.DataFrame()
    df.to_csv(output_csv / 'final' / 'df_final.csv', index=False)
    df.to_pickle(output_pkl / 'final' / 'df_final.pkl')
    final_data.to_csv(output_csv / 'final' / 'grants_final.csv', index=False)
    final_data.to_pickle(output_pkl / 'final' / 'grants_final.pkl')
    final_invest.to_csv(output_csv / 'final' / 'invest_final.csv', index=False)
    final_invest.to_pickle(output_pkl / 'final' / 'invest_final.pkl')
    return df, final_data, final_invest

def create_grant_features(df, icorps, title_column='AwardTitle'):
    """
    Create features for SBIR and STTR awards in a grants DataFrame.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing grant data.
        title_column (str): The column name containing the award titles.

    Returns:
        pd.DataFrame: The DataFrame with new feature columns added.
    """
    # Ensure the title column exists in the DataFrame
    if title_column not in df.columns:
        raise ValueError(f"Column '{title_column}' not found in the DataFrame.")

    # Create new feature columns
    df['sbir'] = df[title_column].str.contains(r'\bSBIR\b', case=False, na=False).astype(int)
    df['sbir_1'] = df[title_column].str.contains(r'\bSBIR Phase I:\b', case=False, na=False).astype(int)
    df['sbir_2'] = df[title_column].str.contains(r'\bSBIR Phase II:\b', case=False, na=False).astype(int)
    df['sttr'] = df[title_column].str.contains(r'\bSTTR\b', case=False, na=False).astype(int)
    df['sttr_1'] = df[title_column].str.contains(r'\bSTTR Phase I:\b', case=False, na=False).astype(int)
    df['sttr_2'] = df[title_column].str.contains(r'\bSTTR Phase II:\b', case=False, na=False).astype(int)
    df['AwardID'] = df['AwardID'].astype(str)
    #merget df with icorps by AwardID
    df = df.merge(icorps, on='AwardID', how='left')
    #fill NaNs with zeros['teams', 'hub', 'site', 'node']
    df['teams'] = df['teams'].fillna(0).astype(int)
    df['hub'] = df['hub'].fillna(0).astype(int)
    df['site'] = df['site'].fillna(0).astype(int)
    df['node'] = df['node'].fillna(0).astype(int)


    return df

def create_invest_features(df, title_column='AwardTitle'):
    """
    Create features for SBIR and STTR awards in a grants DataFrame.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing grant data.
        title_column (str): The column name containing the award titles.

    Returns:
        pd.DataFrame: The DataFrame with new feature columns added.
    """
    # Ensure the title column exists in the DataFrame

    return df

def create_and_sum_icorps_features(df, columns):
    """
    Create a total feature by summing specified columns after filling NaNs with zeros.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame containing I-Corps-related data.
        columns (list): The list of column names to sum.

    Returns:
        pd.DataFrame: The DataFrame with a new 'total_icorps' column added.
    """
    # Fill NaNs with zeros for the specified columns
    for col in columns:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
        else:
            raise ValueError(f"Column '{col}' not found in the DataFrame.")

    # Add a new column for the sum of the specified columns
    df['total_icorps'] = df[columns].sum(axis=1)

    return df


def process_and_merge_grants(grants, other_df, key='AwardID', columns_to_clean=None):
    """
    Merges the grants dataframe with another dataframe on a specified key,
    fills NaN values, and ensures specified columns are cleaned and converted to integers.

    Parameters:
        grants (pd.DataFrame): The main grants dataframe.
        other_df (pd.DataFrame): The dataframe to merge with grants.
        key (str): The key column to merge on (default is 'AwardID').
        columns_to_clean (list): List of column names to clean in the other dataframe.

    Returns:
        pd.DataFrame: Updated grants dataframe after merging and cleaning.
    """
    if columns_to_clean is None:
        columns_to_clean = []

    # Ensure the key column is of type string in both dataframes
    other_df[key] = other_df[key].astype(str)
    grants[key] = grants[key].astype(str)

    # Merge the dataframes
    fields_to_inc=[key]+columns_to_clean
    print("merging dataframes", grants.shape, other_df.shape)
    merged_df = grants.merge(other_df[fields_to_inc], on=key, how='left')
    print("merged", merged_df.shape)
    # Clean and process specified columns
    for col in columns_to_clean:
        if col in merged_df.columns:
            # Fill NaN values with 0
            merged_df[col] = merged_df[col].fillna(0)

            # Ensure all values are integers
            merged_df[col] = merged_df[col].apply(
                lambda x: int(str(x).replace(r'\D', '')) if str(x).isdigit() else 0
            )
            merged_df[col]=merged_df[col].astype(int)

    # Ensure specified columns are of integer type
    #merged_df[columns_to_clean] = merged_df[columns_to_clean].astype(int)

    return merged_df