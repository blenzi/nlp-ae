import streamlit as st
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch

import base64


# @st.cache
# def extract_pdf_page(pdf="tmp.pdf", page=0):
pdf = "tmp.pdf"
with open(pdf, "rb") as f:
    base64_pdf = base64.b64encode(f.read()).decode('utf-8')

# Embedding PDF in HTML
pdf_display = F'<embed src="data:application/pdf;base64,{base64_pdf}" width="600" height="800" type="application/pdf">'

es = Elasticsearch('http://elasticsearch-master:9200')

st.title("**Recherche dans dossier** Etude d'impact Projet PV GUELTAS")

user_input = st.text_area("Search box", "panneaux")

if user_input:
    st.write(f"Searching for: {user_input}")

    m = MultiMatch(query=user_input,
                   fields=["title^3", "text"],  # multiplies title score by 3
                   fuzziness="AUTO")
    s = Search(using=es, index="pdf-index").query(m).highlight("text", fragment_size=200)
    response = s.execute()
    nhits = response.hits.total.value

    # Sort hits
    sort_criteria = st.sidebar.radio('Sort hits by', ['Title order', 'Score'])

    if nhits:
        # Filters
        st.sidebar.markdown("**Filters**")
        pages = sorted(hit.page for hit in response)
        scores = sorted(hit.meta.score for hit in response)
        if len(pages) > 1:
            filter_pages = st.sidebar.slider("Page range", pages[0], pages[-1], (pages[0], pages[-1]), 1)
        if len(scores) > 1:
            filter_score = st.sidebar.slider("Score range", scores[0], scores[-1], (scores[0], scores[-1]))

        if sort_criteria == 'Title order':
            all_hits = sorted(response, key=lambda hit: (hit.page, hit.title))
        else:
            all_hits = sorted(response, key=lambda hit: hit.meta.score, reverse=True)

        selected_hits = [hit for hit in all_hits if
                         (len(pages) <= 1 or filter_pages[0] <= hit.page <= filter_pages[-1])
                         and
                         (len(scores) <= 1 or filter_score[0] <= hit.meta.score <= filter_score[-1])
                        ]
    else:
        selected_hits = all_hits = []

    st.write('Total hits:', nhits, '\n')
    if len(selected_hits) < len(all_hits):
        'Selected hits:', len(selected_hits)
    'Sorting by', sort_criteria.lower()
    show_pdf = st.checkbox('Show PDF')
    '-' * 20

    def show_hits():
        for hit in selected_hits:
            st.write(f"""**Page {hit.page}, score: {hit.meta.score}**""")
            expander = st.expander(hit.title)
            for level, title in enumerate(hit.all_titles):
                expander.write('\t'*level + '- ' + title)
            try:
                for hl in hit.meta.highlight['text']:
                    st.markdown(hl, unsafe_allow_html=True)
            except AttributeError:
                continue
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
