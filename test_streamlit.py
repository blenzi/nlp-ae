import streamlit as st
from elasticsearch import Elasticsearch
import base64



# @st.cache
# def extract_pdf_page(pdf="tmp.pdf", page=0):
pdf="tmp.pdf"
with open(pdf, "rb") as f:
    base64_pdf = base64.b64encode(f.read()).decode('utf-8')

# Embedding PDF in HTML
pdf_display = F'<embed src="data:application/pdf;base64,{base64_pdf}" width="600" height="800" type="application/pdf">'

es = Elasticsearch('http://elasticsearch-master:9200')

st.title("**Recherche dans dossier** Etude d'impact Projet PV GUELTAS")

user_input = st.text_area("Search box", "panneaux")

if user_input:
    res = es.search(index="test-index1", 
                    query={"multi_match": 
                            {"fields": ["title^3", "text"], # multiplies the title score by 3
                             "query": user_input, 
                             "fuzziness": "AUTO"
                            }
                           },
                    highlight={"fields": {"text": {}}}
                   )

    st.write(f"Searching for: {user_input}")
    nhits = res['hits']['total']['value']
    
    # Sort hits
    sort_criteria = st.sidebar.radio('Sort hits by', ['Title order', 'Search rank'])
    
    if nhits:
        # Filters
        st.sidebar.markdown("**Filters**")
        pages = sorted(hit['_source']['page'] for hit in res['hits']['hits'])
        scores = sorted(hit['_score'] for hit in res['hits']['hits'])
        filter_pages = st.sidebar.slider("Page range", pages[0], pages[-1], (pages[0], pages[-1]), 1)
        filter_score = st.sidebar.slider("Score range", scores[0], scores[-1], (scores[0], scores[-1]))
        
        if sort_criteria == 'Title order':
            all_hits = sorted(res['hits']['hits'], key=lambda x: (x['_source']['page'], x['_source']['title']))
        else:
            all_hits = sorted(res['hits']['hits'], key=lambda x: x['_score'], reverse=True)
        
        selected_hits = [hit for hit in all_hits if 
                        filter_pages[0] <= hit['_source']['page'] <= filter_pages[-1] and
                        filter_score[0] <= hit['_score'] <= filter_score[-1]
                        ]
    else:
        selected_hits = all_hits = []
    
    st.write('Total hits:', nhits, '\n')
    if len(selected_hits) < len(all_hits):
        'Selected hits:', len(selected_hits)
    'Sorting by', sort_criteria.lower()
    show_pdf = st.checkbox('Show PDF')
    '-'*20

    def show_hits():
        for hit in selected_hits:
            st.write(f"""**Page {hit['_source']['page']}, score: {hit['_score']}**""")
            expander = st.expander(hit['_source']['title'])
            for level, title in enumerate(hit['_source']['all_titles']):
                expander.write('\t'*level + '- ' + title)
            if 'highlight' in hit:
                for hl in hit['highlight']['text']:
                    st.write(f"{hl.replace('<em>', '**').replace('</em>', '**')}")
            st.write('-'*20, '\n')

    if show_pdf:
        left_column, right_column = st.columns(2)
        with left_column:
            show_hits()
        with right_column:
            # Display PDF
            st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        show_hits()

    
    

