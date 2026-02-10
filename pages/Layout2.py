import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import Parameter_horizontal as Parameter
from sidebar_tempon import build_sidebar


st.set_page_config(page_title="Plan des paramètres", layout="wide")
st.title("Plan des paramètres")

build_sidebar(Parameter)

layout_path = (Path(__file__).resolve().parent.parent / "Plan_Parametres.png").resolve()
if layout_path.exists():
    img_b64 = base64.b64encode(layout_path.read_bytes()).decode("ascii")
    params_html = f"""
    <div style="font-family: sans-serif; color: #222;">
      <div style="margin-bottom: 8px;">Survolez et cliquez sur une zone pour voir les paramètres.</div>
      <div style="border: 1px solid #ccc; display: block; width: 100%;">
        <svg viewBox="0 0 1177 411" style="width: 100%; height: auto; display: block;">
          <image href="data:image/png;base64,{img_b64}" x="0" y="0" width="1177" height="411" />
          <rect x="1099" y="100" width="20" height="20"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="arrivee" style="cursor: pointer;">
            <title>Arrivée (chargement machine 10)</title>
          </rect>
          <rect x="124" y="83" width="600" height="40"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="grenailleuse" style="cursor: pointer;">
            <title>Grenailleuse</title>
          </rect>
          <rect x="83" y="223" width="10" height="60"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="dechargement" style="cursor: pointer;">
            <title>Déchargement vers convoyeur (s)</title>
          </rect>
          <rect x="20" y="194" width="120" height="10"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="tampon" style="cursor: pointer;">
            <title>Tampon</title>
          </rect>
          <rect x="176" y="238" width="80" height="20"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="variable_conv" style="cursor: pointer;">
            <title>Convoyeur variable</title>
          </rect>
          <rect x="251" y="232" width="440" height="20"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="longueur_convoyeur_1" style="cursor: pointer;">
            <title>Longueur convoyeur 1 (cm)</title>
          </rect>
          <rect x="702" y="241" width="10" height="10"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="det_hold_time" style="cursor: pointer;">
            <title>Temps déclenchement détecteurs (s)</title>
          </rect>
          <rect x="814" y="247" width="100" height="10"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="conv_continu" style="cursor: pointer;">
            <title>Convoyeur horizontal continu</title>
          </rect>
          <rect x="883" y="241" width="10" height="10"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="delai_chargement" style="cursor: pointer;">
            <title>Délai de chargement (s)</title>
          </rect>
          <rect x="1027" y="242" width="10" height="10"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="delai_dechargement" style="cursor: pointer;">
            <title>Délai de déchargement (s)</title>
          </rect>
          <rect x="917" y="238" width="60" height="10"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="inspecteur" style="cursor: pointer;">
            <title>Inspecteur</title>
          </rect>
        </svg>
      </div>
      <div id="param-box" style="margin-top: 10px; padding: 8px; border: 1px solid #ddd; background: #f9f9f9;">
        Cliquez sur une zone pour afficher les paramètres.
      </div>
    </div>
    <script>
      function showParams(key) {{
        const box = document.getElementById('param-box');
        if (key === 'arrivee') {{
          box.innerHTML = `
            <b>Paramètres Arrivée</b><br/>
            Intervalle moyen (s): temps entre arrivées des bouteilles sans interruption<br/>
            Probabilité d'arrêt: probabilité sur tout le temps de simulation ou un arret s'arrivera qui dure entre interruption min. et max. <br/>
            Interruption min (s): Maximum temps en plus de intervalle moyen que grenailleuse est a l'arret<br/>
            Interruption max (s): Minimum temps en plus de intervalle moyen que grenailleuse est a l'arret
          `;
        }} else if (key === 'grenailleuse') {{
          box.innerHTML = `
            <b>Paramètres Grenailleuse</b><br/>
            Temps de pas (s)<br/>
            Nombre d'étapes<br/>
            Variation de Vitesse (True/False)
          `;
        }} else if (key === 'dechargement') {{
          box.innerHTML = `
            <b>Déchargement vers convoyeur (s)</b><br/>
            Délai entre sortie grenailleuse et entrée convoyeur
          `;
        }} else if (key === 'tampon') {{
          box.innerHTML = `
            <b>Tampon</b><br/>
            Espacement vertical (cm)<br/>
            Longueur convoyeur 1 (cm)
          `;
        }} else if (key === 'variable_conv') {{
          box.innerHTML = `
            <b>Convoyeur variable</b><br/>
            Temps de pas variable (s)<br/>
            Espacement horizontal (cm)<br/>
            Vitesse convoyeur variable (cm/s)<br/>
            Délai changement mode (s)
          `;
        }} else if (key === 'longueur_convoyeur_1') {{
          box.innerHTML = `
            <b>Longueur convoyeur 1 (cm)</b>
          `;
        }} else if (key === 'det_hold_time') {{
          box.innerHTML = `
            <b>Temps déclenchement détecteurs (s)</b>
          `;
        }} else if (key === 'conv_continu') {{
          box.innerHTML = `
            <b>Convoyeur horizontal continu</b><br/>
            Longueur convoyeur continu (cm)<br/>
            Vitesse convoyeur continu (cm/s)
          `;
        }} else if (key === 'delai_chargement') {{
          box.innerHTML = `
            <b>Délai de chargement (s)</b>
          `;
        }} else if (key === 'delai_dechargement') {{
          box.innerHTML = `
            <b>Délai de déchargement (s)</b>
          `;
        }} else if (key === 'inspecteur') {{
          box.innerHTML = `
            <b>Inspecteur</b><br/>
            Inspection min (s)<br/>
            Inspection max (s)<br/>
            Probabilité pause longue<br/>
            Pause longue min (s)<br/>
            Pause longue max (s)
          `;
        }}
      }}
      const rects = document.querySelectorAll('rect[data-key]');
      rects.forEach((rect) => {{
        rect.addEventListener('click', (e) => {{
          const key = rect.getAttribute('data-key');
          showParams(key);
        }});
      }});
    </script>
    """
    components.html(params_html, height=700, scrolling=True)
else:
    st.warning(f"Layout2.png introuvable: {layout_path}")
