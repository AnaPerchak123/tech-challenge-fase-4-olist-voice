"""Interface local para investigar avaliações com respostas e evidências."""
from pathlib import Path
import json
import streamlit as st
from busca_semantica import BuscaSemantica
from config_api import carregar_config, erro_seguro
from rag_llm import responder, salvar_execucao, formatar_resposta

RAIZ = Path(__file__).resolve().parent
st.set_page_config(page_title="Olist Voice", page_icon="💬", layout="wide")
st.markdown("""<style>
.block-container {max-width:1150px;padding-top:2rem}
[data-testid="stMetricValue"] {color:#137C8B}
</style>""", unsafe_allow_html=True)
st.caption("FIAP · TECH CHALLENGE FASE 4")
st.title("Olist Voice")
st.markdown("Investigue experiências de compra com respostas fundamentadas nas avaliações dos clientes.")


@st.cache_resource
def carregar_busca(versao_manifesto):
    return BuscaSemantica(RAIZ)


manifesto = RAIZ / "chroma_db" / "active_index.json"
if not manifesto.is_file():
    st.info("A base de conhecimento ainda está sendo preparada. Conclua a indexação para abrir as consultas.")
    st.stop()
try:
    with st.spinner("Carregando a base de conhecimento..."):
        motor = carregar_busca(manifesto.stat().st_mtime_ns)
except Exception as erro:
    st.error(erro_seguro(erro))
    st.stop()

a, b, c = st.columns(3)
a.metric("Avaliações disponíveis", f"{motor.info['selected_reviews']:,}".replace(",", "."))
b.metric("Fontes por resposta", "Até 5")
c.metric("Período da base", "2016–2018")
st.caption("Base histórica. Os achados descrevem os relatos recuperados e não representam um ranking de toda a base.")
if motor.info.get("sampling") != "none":
    st.warning("Modo de desenvolvimento: a consulta utiliza uma amostra das avaliações preparadas.")

with st.sidebar:
    st.subheader("Sobre a análise")
    st.write("A aplicação busca comentários relacionados à pergunta e usa essas evidências para elaborar a resposta.")
    st.write("Confira os trechos citados antes de usar um achado em uma decisão.")
    st.caption("Os relatos dos clientes não comprovam, por si só, a causa de um problema.")

sugestoes = ["Escrever minha pergunta", "O que os clientes relatam sobre atraso na entrega?",
             "O que os clientes elogiam sobre a entrega?", "Há relatos de produto diferente do anunciado?",
             "Qual é a política oficial de reembolso da Olist?", "O que é fotossíntese?"]
escolha = st.selectbox("Experimente uma pergunta", sugestoes)
with st.form("consulta"):
    pergunta = st.text_area("O que você deseja investigar?", value="" if escolha == sugestoes[0] else escolha,
                            placeholder="Ex.: O que os clientes relatam sobre problemas na entrega?", max_chars=1500)
    notas = st.multiselect("Notas das avaliações", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5],
                          help="O filtro é aplicado antes da recuperação dos comentários.")
    enviar = st.form_submit_button("Analisar avaliações", type="primary")

if enviar:
    st.session_state.pop("resultado", None)
    st.session_state.pop("erro", None)
    if not pergunta.strip() or not notas:
        st.session_state["erro"] = "Preencha uma pergunta e selecione ao menos uma nota."
    else:
        chave = ""
        try:
            config = carregar_config(RAIZ)
            chave = config.api_key
            with st.spinner("Buscando avaliações e analisando evidências..."):
                resultado = responder(pergunta, motor, RAIZ, notas=notas, config=config)
                salvar_execucao(resultado, RAIZ)
            st.session_state["resultado"] = resultado
        except Exception as erro:
            st.session_state["erro"] = erro_seguro(erro, chave)

if "erro" in st.session_state:
    st.error(st.session_state["erro"])
if "resultado" in st.session_state:
    r = st.session_state["resultado"]
    st.divider()
    st.subheader("Resultado da investigação")
    st.caption("Pergunta analisada: " + r["question"])
    if r["response"]["status"] == "respondido":
        st.markdown(formatar_resposta(r))
    else:
        st.info(formatar_resposta(r))
    usadas = {e["fonte"] for a in r["response"]["achados"] for e in a["evidencias"]}
    if r["sources_sent_to_llm"]:
        st.subheader("Avaliações recuperadas")
        for f in r["sources_sent_to_llm"]:
            meta = f["metadata"]
            citado = " · citada na resposta" if f["label"] in usadas else ""
            with st.expander(f"[{f['label']}] Nota {meta.get('review_score', 'ausente')}{citado}", expanded=f["label"] in usadas):
                st.write(f["text"])
                st.caption(f"Avaliação: {meta['review_id']} · Data: {meta.get('review_date', 'não informada')}")
                st.caption(f"Documento: {f['document_id']}")
                for a in r["response"]["achados"]:
                    for e in a["evidencias"]:
                        if e["fonte"] == f["label"]:
                            st.write("Trecho citado: “" + e["trecho"] + "”")
    st.caption(f"Tempo da consulta após o carregamento: {r['timing_seconds']['total_after_model_loading']:.2f}s")
    st.download_button("Baixar registro da análise", data=json.dumps(r, ensure_ascii=False, indent=2),
                       file_name=f"olist_voice_{r['run_id']}.json", mime="application/json")
