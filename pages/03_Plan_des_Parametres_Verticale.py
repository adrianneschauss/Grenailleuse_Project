import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import Parameter_horizontal as Parameter
from sidebar_verticale import build_sidebar


st.set_page_config(page_title="Plan des paramètres (Verticale)", layout="wide")
st.title("Plan des paramètres (Verticale)")

build_sidebar(Parameter)

layout_path = (Path(__file__).resolve().parent.parent / "Plan_Parametres_Verticale.png").resolve()
if layout_path.exists():
    img_b64 = base64.b64encode(layout_path.read_bytes()).decode("ascii")
    params_html = f"""
    <div style="font-family: sans-serif; color: #222;">
      <div style="margin-bottom: 8px;">Survolez et cliquez sur une zone pour voir les paramètres.</div>
      <div style="border: 1px solid #ccc; display: block; width: 100%;">
        <svg viewBox="0 0 1180 409" style="width: 100%; height: auto; display: block;">
          <image href="data:image/png;base64,{img_b64}" x="0" y="0" width="1180" height="409" />
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
          <rect x="251" y="232" width="440" height="20"
                fill="transparent" stroke="rgba(255,165,0,0.0)"
                data-key="longueur_convoyeur_1" style="cursor: pointer;">
            <title>Convoyeur continu</title>
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
            <b><u>Paramètres Arrivée</u></b><br/>
            <b>Intervalle moyen (s):</b> temps entre deux arrivées, hors interruptions.<br/>
            <b>Probabilité d'arrêt:</b> probabilité qu'un arrêt survienne pendant la simulation; sa durée est comprise entre interruption min. et max.<br/>
            <b>Interruption min (s):</b> durée minimale ajoutée à l'intervalle moyen lorsque la grenailleuse est à l'arrêt.<br/>
            <b>Interruption max (s):</b> durée maximale ajoutée à l'intervalle moyen lorsque la grenailleuse est à l'arrêt.
          `;
        }} else if (key === 'grenailleuse') {{
          box.innerHTML = `
            <b><u>Paramètres Grenailleuse</u></b><br/>
            <b>Temps de pas (s):</b> temps pour faire un pas (distance par pas équivalente à une longueur de bouteille).<br/>
            <b>Nombre d'étapes:</b> nombre d'étapes nécessaires pour qu'une bouteille traverse la grenailleuse.<br/>
            <b>Variation de Vitesse (Vrai/Faux):</b> la grenailleuse adapte automatiquement sa vitesse à partir des détecteurs.<br/>
            <br/>

            <i><b><u>Variation de Vitesse (détails)</u></b><br/>
            La grenailleuse observe en continu les détecteurs (d1, d2, d3).<br/>
            Si d1+d2+d3 restent actifs une grande partie du temps (ligne saturée), elle ralentit en augmentant le temps de pas.<br/>
            Si d1+d2 sont souvent actifs mais d3 ne l’est pas (aval libre), elle accélère en diminuant le temps de pas.<br/>
            Le changement se fait par petites étapes, avec un minimum (0,5x la vitesse normale) et un maximum (2x la vitesse normale), pour rester stable.<br/></i>
          `;
        }} else if (key === 'dechargement') {{
          box.innerHTML = `
            <b><u>Déchargement vers convoyeur (s)</u></b><br/>
            <b>Délai :</b> entre la sortie de la grenailleuse et l’entrée sur le convoyeur, avec déplacement du robot (temps de cycle nécessaire pour partir de la position 0 et y revenir).

          `;
        }} else if (key === 'longueur_convoyeur_1') {{
          box.innerHTML = `
            <b><u>Convoyeur continu</u></b><br/>
            <b>Espacement (cm):</b> distance minimale entre deux bouteilles sur le convoyeur.<br/>
            <b>Vitesse (cm/min):</b> vitesse du convoyeur continu.
          `;
        }} else if (key === 'delai_chargement') {{
          box.innerHTML = `
            <b><u>Délai de chargement (s)</u></b><br/>
            <b>Description:</b> temps pour placer la bouteille sur le poste d'inspection.
          `;
        }} else if (key === 'delai_dechargement') {{
          box.innerHTML = `
            <b><u>Délai de déchargement (s)</u></b><br/>
            <b>Description:</b> temps pour retirer la bouteille du poste d'inspection.
          `;
        }} else if (key === 'inspecteur') {{
          box.innerHTML = `
            <b><u>Inspecteur</u></b><br/>
            <b>Inspection min (s):</b> temps minimum d'inspection (temps normal, sans pause).<br/>
            <b>Inspection max (s):</b> temps maximum d'inspection (temps normal, sans pause).<br/>
            <b>Probabilité pause longue:</b> probabilité que l'inspecteur prenne une pause longue durant la simulation; sa durée est comprise entre pause min. et max.<br/>
            <b>Pause longue min (s):</b> durée minimale de la pause.<br/>
            <b>Pause longue max (s):</b> durée maximale de la pause.
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
    st.warning(f"Plan_Parametres_Verticale.png introuvable: {layout_path}")
