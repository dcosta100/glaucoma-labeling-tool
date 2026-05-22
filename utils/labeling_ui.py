"""
Página de labeling e lógica de cascata.

Regras de cascata (por olho):
  - O 1º campo visual (mais antigo) é a "fonte".
  - Os campos seguintes do mesmo olho espelham automaticamente os rótulos da fonte.
  - Ao editar qualquer rótulo de um campo seguinte, esse campo "desacopla" e passa a
    ser independente (mudanças na fonte deixam de afetá-lo). Os demais continuam
    espelhando. Há um botão para re-acoplar (voltar a copiar da fonte).
"""
from __future__ import annotations

from typing import List

import streamlit as st

from utils import config, data, storage


# ---------------- chaves de session_state ---------------- #

def _eid(maskedid: str, eye: str, vf: int) -> str:
    return f"{maskedid}|{eye}|{vf}"


def _wkey(eid: str, field: str) -> str:
    return f"w|{eid}|{field}"


def _detached() -> dict:
    return st.session_state.setdefault("_detached", {})


def _mark_detached(eid: str) -> None:
    _detached()[eid] = True


# ---------------- inicialização por paciente ---------------- #

def _init_patient(maskedid: str, df_patient) -> None:
    flag = f"_init|{maskedid}"
    if st.session_state.get(flag):
        return

    saved = storage.load_patient_labels(config.LABELER_NAME, maskedid)
    detached = _detached()

    for eye in config.EYES:
        exams = data.exams_by_eye(df_patient, eye)
        for idx, ex in enumerate(exams):
            vf = int(ex["visual_field_number"])
            eid = _eid(maskedid, eye, vf)
            rec = saved.get(f"{eye}|{vf}")
            for f in config.LABEL_FIELDS:
                st.session_state[_wkey(eid, f)] = (
                    rec[f] if rec and f in rec else config.default_value(f)
                )
            # campo seguinte já salvo anteriormente => tratar como independente
            detached[eid] = bool(rec) and idx > 0

    st.session_state[flag] = True


# ---------------- cascata ---------------- #

def _seed_from_source(eid: str, source_eid: str) -> None:
    """Copia os valores da fonte para um campo ainda acoplado (antes de renderizar)."""
    for f in config.LABEL_FIELDS:
        sk = _wkey(source_eid, f)
        if sk in st.session_state:
            st.session_state[_wkey(eid, f)] = st.session_state[sk]


# ---------------- widgets de rótulo ---------------- #

def _selectbox(eid: str, field: str, label: str, container, is_source: bool):
    key = _wkey(eid, field)
    if key not in st.session_state:
        st.session_state[key] = config.default_value(field)
    kwargs = {} if is_source else {"on_change": _mark_detached, "args": (eid,)}
    return container.selectbox(label, config.OPTIONS[field], key=key, **kwargs)


def _render_chain(eid, chain, titles, container, is_source) -> None:
    """Renderiza uma cadeia defeito/posição com revelação progressiva."""
    title_def, title_pos = titles
    for i, (dfield, pfield) in enumerate(chain, start=1):
        dval = _selectbox(eid, dfield, f"{title_def} {i}", container, is_source)
        if dval == "Null":
            break
        _selectbox(eid, pfield, f"{title_pos} {i}", container, is_source)


def _render_exam_labels(eid: str, is_source: bool) -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**General**")
        _selectbox(eid, "normality", "Normality", c1, is_source)
        _selectbox(eid, "reliability", "Reliability", c1, is_source)
    with c2:
        st.markdown("**Glaucomatous**")
        _render_chain(eid, config.G_CHAIN, ("Defect", "Position"), c2, is_source)
    with c3:
        st.markdown("**Non-glaucomatous**")
        _render_chain(eid, config.NG_CHAIN, ("Defect", "Position"), c3, is_source)
    with c4:
        st.markdown("**Artifacts**")
        a1 = _selectbox(eid, "artifact1", "Artifact 1", c4, is_source)
        if a1 != "Null":
            _selectbox(eid, "artifact2", "Artifact 2", c4, is_source)

    ckey = _wkey(eid, "comment")
    if ckey not in st.session_state:
        st.session_state[ckey] = ""
    kwargs = {} if is_source else {"on_change": _mark_detached, "args": (eid,)}
    st.text_input("Comment", key=ckey, **kwargs)


# ---------------- coleta / normalização para salvar ---------------- #

def _normalize_chain(out: dict, chain) -> None:
    stop = False
    for dfield, pfield in chain:
        if stop or out.get(dfield, "Null") == "Null":
            out[dfield] = "Null"
            out[pfield] = "Null"
            stop = True


def _collect_labels(eid: str) -> dict:
    out = {f: st.session_state.get(_wkey(eid, f), config.default_value(f))
           for f in config.LABEL_FIELDS}
    _normalize_chain(out, config.G_CHAIN)
    _normalize_chain(out, config.NG_CHAIN)
    if out.get("artifact1") == "Null":
        out["artifact2"] = "Null"
    return out


# ---------------- exibição de um olho ---------------- #

def _render_eye_column(maskedid: str, eye: str, exams: List[dict]) -> None:
    st.subheader(config.EYE_LABELS[eye])
    if not exams:
        st.info(f"Sem campos visuais para o olho {eye}.")
        return

    source_eid = _eid(maskedid, eye, int(exams[0]["visual_field_number"]))
    detached = _detached()

    for idx, ex in enumerate(exams):
        vf = int(ex["visual_field_number"])
        eid = _eid(maskedid, eye, vf)
        is_source = idx == 0

        # espelha a fonte se ainda estiver acoplado
        if not is_source and not detached.get(eid, False):
            _seed_from_source(eid, source_eid)

        st.markdown(f"#### Field #{vf}")
        meta_bits = [str(ex.get("exam_date", ""))]
        if ex.get("md") not in (None, "", "nan"):
            meta_bits.append(f"MD {ex['md']} dB")
        if ex.get("psd") not in (None, "", "nan"):
            meta_bits.append(f"PSD {ex['psd']} dB")
        if ex.get("vfi") not in (None, "", "nan"):
            meta_bits.append(f"VFI {ex['vfi']}%")
        if ex.get("ght") not in (None, "", "nan"):
            meta_bits.append(f"GHT: {ex['ght']}")
        st.caption("  ·  ".join(b for b in meta_bits if b and b != "nan"))

        img = data.image_path(ex["image_filename"])
        if img.exists():
            st.image(str(img), width="stretch")
        else:
            st.warning(f"Imagem não encontrada: {ex['image_filename']}")

        # status da cascata
        if not is_source:
            if detached.get(eid, False):
                cols = st.columns([3, 1])
                cols[0].caption("✏️ Editado de forma independente")
                if cols[1].button("↻ Copiar do #1", key=f"reattach|{eid}"):
                    detached[eid] = False
                    for f in config.LABEL_FIELDS:
                        st.session_state.pop(_wkey(eid, f), None)
                    st.rerun()
            else:
                st.caption("↳ Copiado automaticamente do Field #1 (edite para destacar)")

        _render_exam_labels(eid, is_source)
        st.divider()


# ---------------- página principal ---------------- #

def labeling_page(df) -> None:
    name = config.LABELER_NAME
    patients = data.list_patients(df)
    total = len(patients)

    completed = storage.get_completed(name)

    # índice do paciente atual: retoma de onde parou (último paciente aberto);
    # se não houver histórico, começa no primeiro ainda não concluído.
    if "patient_idx" not in st.session_state:
        last = storage.get_last_viewed(name)
        if last in patients:
            start = patients.index(last)
        else:
            start = next((i for i, p in enumerate(patients) if p not in completed), 0)
        st.session_state["patient_idx"] = start
    idx = max(0, min(st.session_state["patient_idx"], total - 1))
    maskedid = patients[idx]
    df_patient = df[df["maskedid"] == maskedid]

    # persiste o paciente atual para retomar na próxima sessão
    storage.set_last_viewed(name, maskedid)

    # ----- barra lateral: progresso e navegação ----- #
    with st.sidebar:
        st.markdown(f"### 👤 {name}")
        done = len(completed)
        pct = (done / total * 100) if total else 0
        c1, c2 = st.columns(2)
        c1.metric("Rotulados", f"{done} / {total}")
        c2.metric("Restantes", total - done)
        st.progress(done / total if total else 0)
        st.caption(f"{pct:.0f}% concluído")
        st.divider()

        st.markdown("### Navegação")
        jump = st.selectbox(
            "Ir para paciente",
            options=list(range(total)),
            index=idx,
            format_func=lambda i: f"{'✅ ' if patients[i] in completed else ''}{i + 1}. {patients[i]}",
        )
        if jump != idx:
            st.session_state["patient_idx"] = jump
            st.rerun()

        nav1, nav2 = st.columns(2)
        if nav1.button("← Anterior", width="stretch", disabled=idx == 0):
            st.session_state["patient_idx"] = idx - 1
            st.rerun()
        if nav2.button("Próximo →", width="stretch", disabled=idx >= total - 1):
            st.session_state["patient_idx"] = idx + 1
            st.rerun()

    # ----- cabeçalho ----- #
    age = data.patient_age(df_patient)
    status = "✅ Concluído" if maskedid in completed else ""
    st.markdown(f"## Patient {maskedid} — Age {age}  {status}")
    st.caption(f"Paciente {idx + 1} de {total}")

    _init_patient(maskedid, df_patient)

    # ----- duas colunas: R (esquerda) | L (direita) ----- #
    col_r, col_l = st.columns(2)
    with col_r:
        _render_eye_column(maskedid, "R", data.exams_by_eye(df_patient, "R"))
    with col_l:
        _render_eye_column(maskedid, "L", data.exams_by_eye(df_patient, "L"))

    # ----- ações ----- #
    st.divider()
    b1, b2, b3 = st.columns([1, 1, 2])
    save = b1.button("💾 Salvar", width="stretch")
    save_next = b3.button("✅ Salvar e próximo paciente", type="primary", width="stretch")

    if save or save_next:
        n = _save_patient(name, maskedid, df_patient)
        storage.mark_completed(name, maskedid)
        st.success(f"{n} campo(s) salvo(s) para o paciente {maskedid}.")
        if save_next:
            nxt = idx + 1
            if nxt < total:
                st.session_state["patient_idx"] = nxt
                st.rerun()
            else:
                st.balloons()
                st.success("Todos os pacientes foram percorridos!")


def _save_patient(name: str, maskedid: str, df_patient) -> int:
    count = 0
    for eye in config.EYES:
        for ex in data.exams_by_eye(df_patient, eye):
            vf = int(ex["visual_field_number"])
            eid = _eid(maskedid, eye, vf)
            labels = _collect_labels(eid)
            storage.save_exam_label(name, maskedid, eye, vf, labels, ex)
            count += 1
    return count
