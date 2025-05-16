# mortalite_app.py

from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file.filename.endswith('.xls') or file.filename.endswith('.xlsx'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        df = pd.read_excel(filepath, header=2)

        age = df['Âge x']
        effectif = df['Mixte']
        effectif_femme = df['Femmes']
        effectif_homme = df['Hommes']


        bins = [0, 20, 65, 200]
        labels = ['<20', '20-65', '65+']

        # Conversion en numérique (au cas où)
        df['Âge x'] = pd.to_numeric(df['Âge x'], errors='coerce')
        df = df.dropna(subset=['Âge x'])


        df['tranche'] = pd.cut(df['Âge x'], bins=bins, labels=labels, right=False)

        synthese = df.groupby('tranche', observed=True)['Mixte'].sum().reset_index()
        synthese['effectif'] = synthese['Mixte'] / 1000
        total = synthese['Mixte'].sum()
        synthese['%'] = 100 * synthese['Mixte'] / total

        total_row = pd.DataFrame({
            'tranche': ['Total'],
            'Mixte': [total],
            '%': [100]
        })

        table_data = synthese.to_dict(orient='records')

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=labels[::],  # Pour avoir <20 en bas
            x=synthese.loc[synthese['tranche'] != 'Total', 'Mixte'][::],
            orientation='h',
            marker_color=['#7fc97f', '#ffd92f', '#fd8d3c']
        ))
        fig.update_layout(
            yaxis=dict(title=''),
            xaxis=dict(title='Effectif (en milliers)'),
            plot_bgcolor='#ffffe6',
            paper_bgcolor='#ffffe6'
        )
        bar_html = pio.to_html(fig, full_html=False)


        fig_pyramid = go.Figure()
        fig_pyramid.add_trace(go.Bar(
            y = age,
            x =effectif_femme,
            name = 'Femmes',
            orientation = 'h',
            marker_color = 'orchid'
        ))
        fig_pyramid.add_trace(go.Bar(
            y = age,
            x = -effectif_homme,
            name = 'Hommes',
            orientation = 'h',
            marker_color = 'lightblue'
        ))
        fig_pyramid.update_layout(
            title = 'Pyramide des âges',
            legend_title = 'Sexe',
            barmode = 'relative',
            xaxis=dict(title='Effectif (en milliers)', tickvals=[-400, -200, 0, 200, 400], ticktext=['400', '200', '0', '200', '400']),
            yaxis=dict(title='Âge')
        )
        pyramid_html = pio.to_html(fig_pyramid, full_html=False)
        
        return render_template(
            'results.html',
            bar_plot=bar_html,
            table_data=table_data,
            pyramid_plot=pyramid_html
        )
        
    
    else:
        return "Format de fichier non pris en charge."


def mortalite():
    file = request.files['file']
    if file.filename.endswith('.xls') or file.filename.endswith('.xlsx'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Lecture du fichier Excel
        df = pd.read_excel(filepath, header=2)

        # Extraction des données de survie et d'espérance de vie
        age = df['Âge x']
        survie = df.iloc[:, 5]  # Nombre de survivants à l'âge x
        esperance = df.iloc[:, 6]  # Espérance de vie à l'âge x

        # Création d'un DataFrame avec uniquement l'âge et la survie
        df_survie = pd.DataFrame({
            'Age': age,
            'Survie': survie
        })

        # Filtrer pour ne garder que les âges multiples de 5 (et 0)
        df_survie_5ans = df_survie[df_survie['Age'].isin([0] + list(range(5, 105, 5)))]

        # Création du graphique de survie en bâtons
        fig_survie = go.Figure()
        fig_survie.add_trace(go.Bar(
            x=df_survie_5ans['Age'],
            y=df_survie_5ans['Survie'],
            name='Survivants',
            marker_color='blue'
        ))
        fig_survie.update_layout(
            title='Nombre de survivants par tranche de 5 ans',
            xaxis=dict(
                title='Âge',
                tickmode='array',
                tickvals=list(range(0, 105, 5)),
                ticktext=[str(x) for x in range(0, 105, 5)]
            ),
            yaxis=dict(title='Nombre de survivants'),
            plot_bgcolor='white',
            bargap=0.2
        )
        survie_html = pio.to_html(fig_survie, full_html=False)

        # Création du graphique d'espérance de vie
        fig_esperance = go.Figure()
        fig_esperance.add_trace(go.Scatter(
            x=age,
            y=esperance,
            mode='lines',
            name='Espérance de vie',
            line=dict(color='green')
        ))
        fig_esperance.update_layout(
            title='Espérance de vie selon l\'âge',
            xaxis=dict(title='Âge'),
            yaxis=dict(title='Espérance de vie (années)'),
            plot_bgcolor='white'
        )
        esperance_html = pio.to_html(fig_esperance, full_html=False)

        # Création d'un tableau de synthèse avec les données par tranches de 5 ans
        synthese = pd.DataFrame({
            'Âge': df_survie_5ans['Age'],
            'Survivants': df_survie_5ans['Survie'].round(0),
            'Espérance de vie': esperance[df_survie_5ans.index].round(2)
        })
        table_data = synthese.to_dict(orient='records')

        return render_template(
            'mortalite.html',
            survie_plot=survie_html,
            esperance_plot=esperance_html,
            table_data=table_data
        )
    else:
        return "Format de fichier non pris en charge."

@app.route('/upload_demo', methods=['POST'])
def upload_demo():
    # Même logique que dans /upload pour l'instant
    return upload()

@app.route('/upload_mortalite', methods=['POST'])
def upload_mortalite():
    # Pour l'instant, tu peux copier la logique de /upload ou mettre un message temporaire
    return mortalite()

if __name__ == '__main__':
    app.run(debug=True)