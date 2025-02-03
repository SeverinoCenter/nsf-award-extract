from sentence_transformers import SentenceTransformer
import torch
import pandas as pd



def load_model(model_name='all-MiniLM-L6-v2'):
    """Load a pre-trained SentenceTransformer model."""
    return SentenceTransformer(model_name)

def encode_texts(model, texts):
    """Encode a list of texts into embeddings using a SentenceTransformer model."""
    return model.encode(texts, convert_to_tensor=True)

def find_closest_match(name, model, search_space_embeddings, search_space_df, return_columns):
    """Find the closest match for a given name using cosine similarity."""
    try:
        query_embedding = model.encode(name, convert_to_tensor=True)
        similarities = torch.nn.functional.cosine_similarity(query_embedding, search_space_embeddings, dim=1)
        closest_idx = torch.argmax(similarities).item()
        
        #result = {'Similarity_Score': similarities[closest_idx].item(), 'Matched_Name': search_space_df.iloc[closest_idx][match_column_search]}
        result = {'Similarity_Score': similarities[closest_idx].item()}
        for col in return_columns:
            result[col] = search_space_df.iloc[closest_idx][col]
        
        return result
    except Exception as e:
        print(f"Error processing {name}: {e}")
        return None

def batch_process_matches(df, search_space_df, model, match_column_df, match_column_search, return_columns_df, return_columns_search, batch_size=100, max_records=None, output_path="match_results.xlsx"):
    """Process a DataFrame in batches to find the closest match for each entry, limited to max_records if specified."""
    search_space_embeddings = encode_texts(model, search_space_df[match_column_search].tolist())
    results = []
    
    for i, row in enumerate(df.itertuples(index=False), start=1):
        if max_records and i > max_records:
            break
        
        match_result = find_closest_match(getattr(row, match_column_df), model, search_space_embeddings, search_space_df, return_columns_search)
        if match_result:
            results.append([getattr(row, col) for col in return_columns_df] + [match_result[col] for col in return_columns_search] + [match_result['Similarity_Score']])
        
        if i % batch_size == 0:
            print(f"Processed {i} records, saving progress...")
            temp_df = pd.DataFrame(results, columns=return_columns_df  + return_columns_search + ['Similarity_Score'])
            #temp_df.to_csv(f"progress_{i}.csv", index=False)
    
    print("Final save...")
    final_df = pd.DataFrame(results, columns=return_columns_df  + return_columns_search + ['Similarity_Score'])
    #if final_df['Similarity_Score'] =1, set match to 1, else set to null:
    final_df['Match'] = final_df['Similarity_Score'].apply(lambda x: 1 if x >= 0.99 else None)
    with pd.ExcelWriter(output_path) as writer:
        final_df.to_excel(writer, sheet_name="MatchResults", index=False)
        search_space_df.to_excel(writer, sheet_name="SearchSpace", index=False)
    return final_df
# from sentence_transformers import SentenceTransformer
# import torch
# import pandas as pd

# def load_model(model_name='all-MiniLM-L6-v2'):
#     """Load a pre-trained SentenceTransformer model."""
#     return SentenceTransformer(model_name)

# def encode_texts(model, texts):
#     """Encode a list of texts into embeddings using a SentenceTransformer model."""
#     return model.encode(texts, convert_to_tensor=True)

# def find_closest_match(name, model, search_space_embeddings, search_space_df, return_columns=['INSTNM', 'AUTM_ID']):
#     """Find the closest match for a given name using cosine similarity."""
#     try:
#         query_embedding = model.encode(name, convert_to_tensor=True)
#         similarities = torch.nn.functional.cosine_similarity(query_embedding, search_space_embeddings, dim=1)
#         closest_idx = torch.argmax(similarities).item()
        
#         result = {'Similarity_Score': similarities[closest_idx].item()}
#         for col in return_columns:
#             result[col] = search_space_df.iloc[closest_idx][col]
        
#         return result
#     except Exception as e:
#         print(f"Error processing {name}: {e}")
#         return None

# def batch_process_matches(df, search_space_df, model, batch_size=100, output_path="match_results.xlsx"):
#     """Process a DataFrame in batches to find the closest match for each entry."""
#     search_space_embeddings = encode_texts(model, search_space_df['INSTNM'].tolist())
#     results = []
    
#     for i, (name, org_uei) in enumerate(zip(df['Institution_Name_C'], df['Institution_OrgUEINum_C']), start=1):
#         match_result = find_closest_match(name, model, search_space_embeddings, search_space_df)
#         if match_result:
#             results.append((name, org_uei, match_result['INSTNM'], match_result['AUTM_ID'], match_result['Similarity_Score']))
        
#         if i % batch_size == 0:
#             print(f"Processed {i} records, saving progress...")
#             temp_df = pd.DataFrame(results, columns=['Institution_Name_C', 'Institution_OrgUEINum_C', 'Closest_Match', 'AUTM_ID', 'Similarity_Score'])
#             temp_df.to_csv(f"progress_{i}.csv", index=False)
    
#     print("Final save...")
#     final_df = pd.DataFrame(results, columns=['Institution_Name_C', 'Institution_OrgUEINum_C', 'Closest_Match', 'AUTM_ID', 'Similarity_Score'])
#     with pd.ExcelWriter(output_path) as writer:
#         final_df.to_excel(writer, sheet_name="MatchResults", index=False)
#         search_space_df.to_excel(writer, sheet_name="SearchSpace", index=False)
#     return final_df
