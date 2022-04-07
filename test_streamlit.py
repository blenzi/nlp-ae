import streamlit as st
from elasticsearch import Elasticsearch


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
    
    # Sort hits
    sort_criteria = st.sidebar.radio('Sort hits by', ['Title order', 'Search rank'])
    
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
    st.write('Total hits:', res['hits']['total']['value'], '\n')
    if len(selected_hits) < len(all_hits):
        'Selected hits:', len(hits)
    'Sorting by', sort_criteria.lower()
    '-'*20
    
    for hit in selected_hits:
        st.write(f"""Page {hit['_source']['page']}, section {hit['_source']['title']}, score: {hit['_score']}""")
        for hl in hit['highlight']['text']:
            st.write(f"{hl.replace('<em>', '**').replace('</em>', '**')}")
        st.write('-'*20, '\n')




    
    

