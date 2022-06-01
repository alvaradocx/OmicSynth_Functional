import streamlit as st
import pandas as pd


def convert_df(df):
     # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return df.to_csv(index = False)

def create_df(df, diseases, omics):
  # determine max possible options 
  dx_max = len(df['Disease'])
  o_max = len(df['Omic'].unique())

  # num of options in provided lists
  dx_len = len(diseases)
  o_len = len(omics)

  if dx_len == dx_max and o_max == o_len:
    return df

  elif dx_len == dx_max:
    new_df = df[df['Omic'].isin(omics)]
    return new_df

  elif o_max == o_len:
    new_df = df[df['Disease'].isin(diseases)]
    return new_df
  
  else:
    new_df = df.query("Disease in @diseases and Omic in @omics")
    return new_df

def pull_snp_count(input_df, p_smr_multi = None, p_HEIDI = None, count = False, *snps):
    # filter df for user defined p_values if provided
    if p_smr_multi != None and p_HEIDI != None:
        filter_df = input_df.query(f'p_SMR_multi < {p_smr_multi} & p_SMR_multi != -9999.000000 & p_HEIDI > {p_HEIDI} & p_HEIDI != -9999.000000').sort_values('p_HEIDI', ascending = False)
    else:
        filter_df = input_df.query('p_SMR_multi != -9999.000000 & p_HEIDI != -9999.000000').sort_values('p_HEIDI', ascending = False)
    # narrow down to main columns of interest
    filter_df = filter_df[['Omic', 'Disease', 'Gene_rename', 'topSNP', 'b_GWAS','p_GWAS', 'b_SMR', 'p_SMR_multi', 'p_HEIDI']]
    
    # filter for genes
    final_df = pd.DataFrame()
    for snps in snps:
        df = filter_df.query(f"topSNP == '{snp}'")
        final_df = pd.concat([final_df,df])
    
    final_df.sort_values('p_HEIDI', ascending = False, inplace = True)
    final_df_fil = final_df.set_index(['topSNP', 'Disease', 'Omic']).sort_index()
    
    if count == True:
        final_df.sort_values('Omic', ascending = False, inplace = True)
        final_df_count = final_df.groupby(['topSNP', 'Omic']).count()
        return final_df_fil, final_df_count
    else:
        return final_df_fil

def app():
    # CSS to inject contained in a string
    #hide_dataframe_row_index = """<style>.row_heading.level0 {display:none}.blank {display:none}</style>"""

    # Inject CSS with Markdown
    #st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)

    # session state variables for  gene dataframe
    if 'snps_list' not in st.session_state: # genes in dataase
        st.session_state['snps_list'] = None
    if 'snp_results_df' not in st.session_state:
        st.session_state['snp_results_df'] = None

    # session state variables for parameter buttons
    
    if 'omic_count' not in st.session_state:
        st.session_state['omic_count'] = False
    if 'dx_count' not in st.session_state:
        st.session_state['dx_count'] = False
    
    # session state variables forcount dfs
    if 'omic_df' not in st.session_state:
        st.session_state['omic_df'] = False
    if 'dx_df' not in st.session_state:
        st.session_state['dx_df'] = False
    
    
    # parameter session state
    if 'pval' not in st.session_state:
        st.session_state['pval'] = 0.05
    if 'heidi' not in st.session_state:
        st.session_state['heidi'] = 0.01
    if 'snps' not in st.session_state:
        st.session_state['snps'] = ''
    if 'z_status' not in st.session_state:
        st.session_state['z_status'] = 'not_run'
    


    # session state variables for z-score copmutation
    
    # if 'z_df' not in st.session_state:
    #     st.session_state['mtc_df'] = None
    

    main_df = st.session_state['main_data']
    main_snp_list = list(main_df['topSNP'].unique())
    st.session_state['snps_list']  = main_snp_list

    st.title('SNP Searchh')
    st.write("Use this interactive tool to search for your SNP(s) of interest against our database.")
    
    with st.form("SNP_Search"):
        st.subheader('Parameter Selection')

        # user input - snps list
        snps_list = st.text_area('Input a SNP or list of SNPs (seperated by comma):')
        # split list
        snps_list = snps_list.split(',')
        new_snps = []
        for snp in snps_list:
            new_snps.append(snp.strip())

        st.session_state['snps'] = new_snps # add to session state

        # user -  p_val and heidi
        pvalue = st.number_input('P-value threshold', value = 0.05)
        st.session_state['pval'] = pvalue

        heidival = st.number_input('HEIDI p-value threshold', value = 0.01)
        st.session_state['heidi'] = heidival


        # return count df
        count_omic = st.radio('Would you like to return a dataframe that shows how many times a SNP shows up in each omic?', ('Yes', 'No'))
        st.session_state['omic_count'] = count_omic
        count_dx = st.radio('Would you like to return a dataframe that shows how many times a SNP shows up in each disease?', ('Yes', 'No'))
        st.session_state['dx_count'] = count_dx


        submitted = st.form_submit_button("Search!")
        
        
    if submitted:
        st.session_state['z_status'] = 'run'

    if st.session_state['z_status'] == 'run':
        # make sure snp list is correct
        not_snps = []
        for snp in st.session_state['snps']:
            if snp not in st.session_state['snps_list']:
                not_snps.append(snp)
        
        if len(not_snps) >= 2:
            st.write(f'{", ".join(not_snps)} are not recognized or are not in our dataset. Please check your list and try again.')
        elif len(not_snps) == 1:
            st.write(f'{not_snps[0]} is not recognized or is not in our dataset. Please check and try again.')
        else:
            snp_results_df = main_df[main_df['topSNP'].isin(st.session_state['snps'])]
            p_val = st.session_state['pval']
            heidi_val = st.session_state['heidi']
            snp_results_df = snp_results_df.query(f'p_SMR_multi < {p_val} & p_HEIDI > {heidi_val}')
            st.session_state['snp_results_df'] = snp_results_df
            st.subheader('Results dataframe')
            st.dataframe(st.session_state['snp_results_df'])

            st.download_button(label="Download results as CSV", data=convert_df(st.session_state['snp_results_df']), mime='text/csv')

        if st.session_state['omic_count'] == 'Yes' and st.session_state['dx_count'] == 'Yes':
            # omic count
            omic_count_df = pd.crosstab(st.session_state['snp_results_df'].Omic, st.session_state['snp_results_df'].topSNP)
            st.session_state['omic_df'] = omic_count_df
            st.subheader('Omic count')
            st.dataframe(st.session_state['omic_df'])
            
            st.download_button(label="Download omic count results as CSV", data=convert_df(st.session_state['omic_df']), mime='text/csv')

            # disease count
            dx_count_df = pd.crosstab(st.session_state['snp_results_df'].Disease, st.session_state['snp_results_df'].topSNP)
            st.session_state['dx_df'] = dx_count_df
            st.subheader('Disease count')
            st.dataframe(st.session_state['dx_df'])

            st.download_button(label="Download disease count results as CSV", data=convert_df(st.session_state['dx_df']), mime='text/csv')

        elif st.session_state['omic_count'] == 'Yes' and st.session_state['dx_count'] == 'No':
            # omic count
            omic_count_df = pd.crosstab(st.session_state['snp_results_df'].Omic, st.session_state['snp_results_df'].topSNP)
            st.session_state['omic_df'] = omic_count_df
            st.subheader('Omic count')
            st.dataframe(st.session_state['omic_df'])

            st.download_button(label="Download omic count results as CSV", data=convert_df(st.session_state['omic_df']), mime='text/csv')

        elif st.session_state['omic_count'] == 'No' and st.session_state['dx_count'] == 'Yes':
            # disease count
            dx_count_df = pd.crosstab(st.session_state['snp_results_df'].Disease, st.session_state['snp_results_df'].topSNP)
            st.session_state['dx_df'] = dx_count_df
            st.subheader('Disease count')
            st.dataframe(st.session_state['dx_df'])

            st.download_button(label="Download disease count results as CSV", data=convert_df(st.session_state['dx_df']), mime='text/csv')
