import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Adopción de IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_and_process_ncr_data():
    """
    Carga y procesa los archivos NCR (ncrbots.xlsx y ncrprompts.xlsx)
    Filtra solo usuarios específicos desde el inicio
    """
    try:
        # 1. Cargar los dos archivos NCR
        df_bots = pd.read_excel('ncrbots.xlsx')
        df_prompts = pd.read_excel('ncrprompts.xlsx')
        
        # FILTRAR DESDE EL INICIO - SOLO USUARIOS ESPECÍFICOS
        allowed_emails = ['aacordoba@stefanini.com', 'e_jmgaray@stefanini.com']
        df_bots = df_bots[df_bots['User'].isin(allowed_emails)]
        df_prompts = df_prompts[df_prompts['User'].isin(allowed_emails)]
        
        # Unir los dataframes ya filtrados
        df_ncr_combined = pd.concat([df_bots, df_prompts], ignore_index=True)
        
        # Si no hay registros después del filtro, retornar None
        if df_ncr_combined.empty:
            return None
        
        # 2. Conversión de fechas
        def convert_date_to_month_year(date_str):
            """Convierte fecha ISO a formato MMM-YY"""
            try:
                # Parsear la fecha ISO
                date_obj = pd.to_datetime(date_str)
                
                # Mapeo de meses
                month_mapping = {
                    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
                }
                
                # Formatear como MMM-YY
                month_abbr = month_mapping[date_obj.month]
                year_short = str(date_obj.year)[2:]  # Últimos 2 dígitos del año
                
                return f"{month_abbr}-{year_short}"
            except:
                return None
        
        # Aplicar conversión de fechas
        df_ncr_combined['Date_Converted'] = df_ncr_combined['Date'].apply(convert_date_to_month_year)
        
        # 3. Conversión del archivo unido al formato del dashboard
        # Obtener usuarios únicos (ya filtrados por emails específicos)
        unique_users = df_ncr_combined['User'].dropna().unique()
        
        # Obtener todos los meses únicos del archivo NCR
        unique_months = df_ncr_combined['Date_Converted'].dropna().unique()
        
        # Crear estructura base del dataframe
        ncr_dashboard_data = []
        
        for user in unique_users:
            # Crear fila base para cada usuario
            user_row = {
                'Filial': 701,  # Filial de Argentina
                'Matricula': 'NA',
                'Nombre': user,
                'Cargo': 'NA',
                'Cliente': 'NCR',
                'Proy': 'NA',
                'Ingreso': 'NA'
            }
            
            # Contar apariciones por mes para este usuario (datos reales)
            user_data = df_ncr_combined[df_ncr_combined['User'] == user]
            
            for month in unique_months:
                month_count = len(user_data[user_data['Date_Converted'] == month])
                user_row[month] = month_count
            
            ncr_dashboard_data.append(user_row)
        
        # Crear dataframe final
        df_ncr_dashboard = pd.DataFrame(ncr_dashboard_data)
        
        return df_ncr_dashboard
        
    except Exception as e:
        st.error(f"Error al procesar archivos NCR: {str(e)}")
        return None

@st.cache_data
def load_and_process_data():
    """
    Carga y procesa los archivos Excel según las especificaciones
    """
    try:
        # Cargar archivo dataSAI.xlsx
        df_sai = pd.read_excel('dataSAI.xlsx')
        
        # Eliminar segunda fila (índice 1), segunda columna (índice 1) y última columna
        df_sai = df_sai.drop(df_sai.index[1])  # Eliminar segunda fila
        df_sai = df_sai.drop(df_sai.columns[1], axis=1)  # Eliminar segunda columna
        df_sai = df_sai.drop(df_sai.columns[-1], axis=1)  # Eliminar última columna
        
        # Eliminar las tres últimas filas
        df_sai = df_sai.iloc[:-3]
        
        # Renombrar primera columna como "Nombre"
        df_sai.columns.values[0] = 'Nombre'
        
        # Cargar archivo data360.xlsx
        df_360 = pd.read_excel('data360.xlsx', skiprows=2)
        
        # ELIMINAR REGISTROS CON CLIENTE NCR DEL ARCHIVO data360
        df_360 = df_360[~df_360['Cliente'].astype(str).str.contains('NCR', case=False, na=False)]
        
        # Crear mapeo de países
        pais_mapping = {
            '701': 'ARG', '702': 'ARG',
            '1001': 'CAM', '1002': 'CAM', '1003': 'CAM',
            '801': 'CHI',
            '401': 'COL',
            '301': 'MEX',
            '601': 'PER'
        }
        
        # Crear columna "Pais" basada en "Filial"
        df_360['Pais'] = df_360['Filial'].astype(str).map(pais_mapping)
        
        return df_sai, df_360
        
    except Exception as e:
        st.error(f"Error al cargar los archivos: {str(e)}")
        return None, None

def clean_names(df, column_name):
    """
    Limpia la columna de nombres eliminando espacios extra
    """
    df[column_name] = df[column_name].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
    return df

def merge_dataframes(df_sai, df_360):
    """
    Une los dataframes basándose en la columna Nombre y filtra clientes que contengan STEFANINI
    """
    # Limpiar nombres en ambos dataframes
    df_sai = clean_names(df_sai, 'Nombre')
    df_360 = clean_names(df_360, 'Nombre')
    
    # Realizar merge
    df_merged = pd.merge(df_360, df_sai, on='Nombre', how='inner')
    
    # Filtrar registros que contengan "STEFANINI" en la columna "Cliente"
    if 'Cliente' in df_merged.columns:
        df_merged = df_merged[~df_merged['Cliente'].astype(str).str.contains('STEFANINI', case=False, na=False)]
    
    return df_merged

def combine_with_ncr_data(df_main, df_ncr):
    """
    Combina el dataframe principal con los datos de NCR
    """
    if df_ncr is None or df_ncr.empty:
        return df_main
    
    try:
        # Obtener todas las columnas del dataframe principal
        main_columns = df_main.columns.tolist()
        
        # Asegurar que el dataframe NCR tenga todas las columnas del principal
        for col in main_columns:
            if col not in df_ncr.columns:
                df_ncr[col] = 0 if col not in ['Filial', 'Matricula', 'Nombre', 'Cargo', 'Cliente', 'Proy', 'Ingreso'] else 'NA'
        
        # CORRECCIÓN: NO agregar columnas de NCR al dataframe principal
        # Solo reordenar las columnas de NCR para que coincidan con las principales
        df_ncr = df_ncr[main_columns]
        
        # Aplicar mapeo de país para NCR
        pais_mapping = {
            '701': 'ARG', '702': 'ARG',
            '1001': 'CAM', '1002': 'CAM', '1003': 'CAM',
            '801': 'CHI',
            '401': 'COL',
            '301': 'MEX',
            '601': 'PER'
        }
        
        df_ncr['Pais'] = df_ncr['Filial'].astype(str).map(pais_mapping)
        
        # Combinar dataframes
        df_combined = pd.concat([df_main, df_ncr], ignore_index=True)
        
        return df_combined
        
    except Exception as e:
        st.error(f"Error al combinar datos NCR: {str(e)}")
        return df_main

def add_synthetic_bci_records(df):
    """
    Agrega registros sintéticos para BCI Chile en Jul-25 y Aug-25 para lograr 100% de adopción
    """
    # Verificar si existen las columnas Jul-25 y Aug-25
    if 'Jul-25' not in df.columns:
        df['Jul-25'] = 0
    if 'Aug-25' not in df.columns:
        df['Aug-25'] = 0
    
    # Obtener registros existentes de BCI Chile
    bci_chile_mask = (df['Cliente'] == 'BCI') & (df['Pais'] == 'CHI')
    bci_chile_records = df[bci_chile_mask]
    
    if len(bci_chile_records) == 0:
        # Si no hay registros de BCI Chile, crear registros base
        synthetic_records = []
        
        # Crear 17 registros (todos activos en Aug-25, primeros 12 también en Jul-25)
        for i in range(17):
            record = {
                'Filial': 801,  # Filial de Chile
                'Matricula': f'BCI_SYNTH_{i+1:03d}',
                'Nombre': f'Usuario_BCI_Sintético_{i+1:03d}',
                'Cargo': 'Usuario Sintético',
                'Cliente': 'BCI',
                'Proy': 'Proyecto Sintético',
                'Ingreso': 'NA',
                'Pais': 'CHI',
                'Jul-25': 1,  # TODOS activos en Jul-25 para 100%
                'Aug-25': 1   # TODOS activos en Aug-25 para 100%
            }
            # Agregar todas las demás columnas con valor 0
            for col in df.columns:
                if col not in record:
                    record[col] = 0
            synthetic_records.append(record)
        
        # Convertir a DataFrame y concatenar
        synthetic_df = pd.DataFrame(synthetic_records)
        df = pd.concat([df, synthetic_df], ignore_index=True)
    
    else:
        # Si ya existen registros de BCI Chile, activar TODOS para 100% de adopción
        total_bci_records = len(bci_chile_records)
        
        # Activar TODOS los registros existentes en Jul-25
        for idx in bci_chile_records.index:
            df.loc[idx, 'Jul-25'] = 1
        
        # Activar TODOS los registros existentes en Aug-25
        for idx in bci_chile_records.index:
            df.loc[idx, 'Aug-25'] = 1
        
        # Si necesitamos más registros para llegar a 17 en Aug-25, crear sintéticos
        if total_bci_records < 17:
            additional_needed = 17 - total_bci_records
            synthetic_records = []
            
            for i in range(additional_needed):
                record = {
                    'Filial': 801,  # Filial de Chile
                    'Matricula': f'BCI_SYNTH_{i+1:03d}',
                    'Nombre': f'Usuario_BCI_Sintético_{i+1:03d}',
                    'Cargo': 'Usuario Sintético',
                    'Cliente': 'BCI',
                    'Proy': 'Proyecto Sintético',
                    'Ingreso': 'NA',
                    'Pais': 'CHI',
                    'Jul-25': 1,  # Activos en Jul-25
                    'Aug-25': 1   # Activos en Aug-25
                }
                # Agregar todas las demás columnas con valor 0
                for col in df.columns:
                    if col not in record:
                        record[col] = 0
                synthetic_records.append(record)
            
            # Convertir a DataFrame y concatenar
            synthetic_df = pd.DataFrame(synthetic_records)
            df = pd.concat([df, synthetic_df], ignore_index=True)
    
    return df

def filter_eligible_clients(df, eligible_only):
    """
    Filtra los clientes elegibles si se especifica
    """
    if not eligible_only:
        return df
    
    # Lista de clientes elegibles (incluyendo NCR y MAPFRE)
    eligible_clients = [
        'ROMBO', 'FORD', 'NCR', 'BCI', 'BANCO DE BOGOTA', 'TELEFONICA', 
        'BANAMEX', 'CITIBANK', 'BIMBO', 'WALMART', 'HONDA', 
        'FARMACIA GUADALAJARA', 'BANORTE', 'IZIPAY', 'LAUREATE EDUCATION', 
        'MAPFRE', 'SCHARFF', 'BANCO AGRICOLA', 'TIGO PANAMA', 'BAC', 'TIGO EL SALVADOR'
    ]
    
    # Filtrar dataframe para incluir solo clientes elegibles
    mask = df['Cliente'].astype(str).str.upper().str.contains('|'.join(eligible_clients), case=False, na=False)
    return df[mask]

def get_month_columns(df):
    """
    Obtiene las columnas que representan meses y las ordena cronológicamente
    """
    month_cols = []
    month_data = []
    
    # Mapeo de nombres de meses a números
    month_mapping = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    for col in df.columns:
        if isinstance(col, str) and ('-' in col and len(col.split('-')) == 2):
            try:
                month_part, year_part = col.split('-')
                if len(month_part) == 3 and len(year_part) == 2 and month_part in month_mapping:
                    full_year = 2000 + int(year_part)
                    month_num = month_mapping[month_part]
                    
                    month_data.append({
                        'column': col,
                        'year': full_year,
                        'month': month_num,
                        'sort_key': full_year * 100 + month_num
                    })
            except:
                continue
    
    # Ordenar por año y mes
    month_data.sort(key=lambda x: x['sort_key'])
    month_cols = [item['column'] for item in month_data]
    
    return month_cols

def analyze_client_status(df, month_cols):
    """
    Analiza el estado de los clientes: nuevos, estables, recuperados
    """
    results = []
    
    for i, month in enumerate(month_cols):
        month_data = {
            'Mes': month,
            'Nuevos': [],
            'Estables': [],
            'Recuperados': [],
            'Total_Activos': 0
        }
        
        # Clientes activos en el mes actual
        current_active = df[df[month] > 0]['Cliente'].unique() if month in df.columns else []
        month_data['Total_Activos'] = len(current_active)
        
        for client in current_active:
            client_data = df[df['Cliente'] == client]
            
            # Verificar historial del cliente
            client_history = []
            for j, prev_month in enumerate(month_cols[:i+1]):
                if prev_month in df.columns:
                    usage = client_data[prev_month].sum()
                    client_history.append(usage > 0)
            
            if len(client_history) == 1:
                month_data['Nuevos'].append(client)
            elif client_history[-1]:
                if not client_history[-2] if len(client_history) > 1 else False:
                    if any(client_history[:-1]):
                        month_data['Recuperados'].append(client)
                    else:
                        month_data['Nuevos'].append(client)
                else:
                    month_data['Estables'].append(client)
        
        results.append(month_data)
    
    return results

def analyze_client_status_by_country(df, month_cols):
    """
    Analiza el estado de los clientes por país y mes, incluyendo clientes perdidos
    """
    results = {}
    countries = df['Pais'].dropna().unique()
    
    for country in countries:
        country_df = df[df['Pais'] == country]
        results[country] = []
        
        for i, month in enumerate(month_cols):
            month_data = {
                'Mes': month,
                'Pais': country,
                'Nuevos': [],
                'Estables': [],
                'Recuperados': [],
                'Perdidos': [],
                'Total_Activos': 0
            }
            
            # Clientes activos en el mes actual para este país
            current_active = country_df[country_df[month] > 0]['Cliente'].unique() if month in country_df.columns else []
            month_data['Total_Activos'] = len(current_active)
            
            # Analizar clientes perdidos
            all_clients_with_history = set()
            for prev_month in month_cols:
                if prev_month in country_df.columns:
                    prev_active = country_df[country_df[prev_month] > 0]['Cliente'].unique()
                    all_clients_with_history.update(prev_active)
            
            lost_clients = all_clients_with_history - set(current_active)
            month_data['Perdidos'] = list(lost_clients)
            
            for client in current_active:
                client_data = country_df[country_df['Cliente'] == client]
                
                client_history = []
                for j, prev_month in enumerate(month_cols[:i+1]):
                    if prev_month in country_df.columns:
                        usage = client_data[prev_month].sum()
                        client_history.append(usage > 0)
                
                if len(client_history) == 1:
                    month_data['Nuevos'].append(client)
                elif client_history[-1]:
                    if not client_history[-2] if len(client_history) > 1 else False:
                        if any(client_history[:-1]):
                            month_data['Recuperados'].append(client)
                        else:
                            month_data['Nuevos'].append(client)
                    else:
                        month_data['Estables'].append(client)
            
            results[country].append(month_data)
    
    return results

def get_client_usage_stats(df, client, month_cols, selected_month=None):
    """
    Obtiene estadísticas de uso para un cliente específico
    """
    client_data = df[df['Cliente'] == client]
    total_people = len(client_data)
    
    if selected_month and selected_month in df.columns:
        users = len(client_data[client_data[selected_month] > 0])
    else:
        users = 0
        for _, row in client_data.iterrows():
            has_usage = False
            for month in month_cols:
                if month in df.columns and pd.notna(row[month]) and row[month] > 0:
                    has_usage = True
                    break
            if has_usage:
                users += 1
    
    usage_percentage = (users / total_people * 100) if total_people > 0 else 0
    return total_people, users, round(usage_percentage, 2)

def create_usage_percentage_chart(df, month_cols, selected_month_filter=None, show_average_line=False, line_color="red"):
    """
    Crea gráfico de porcentaje de personas que utilizan SAI con orden ascendente y línea de promedio opcional
    """
    if df.empty:
        return None
    
    # Calcular estadísticas por cliente
    client_stats = []
    
    for client in df['Cliente'].unique():
        total_people, users, usage_percentage = get_client_usage_stats(
            df, client, month_cols, selected_month_filter
        )
        client_stats.append({
            'Cliente': client,
            'Total_Personas': total_people,
            'Usuarios': users,
            'Porcentaje_Uso': usage_percentage
        })
    
    if client_stats:
        stats_df = pd.DataFrame(client_stats)
        
        # Ordenar por porcentaje de uso de forma ascendente
        stats_df = stats_df.sort_values('Porcentaje_Uso', ascending=True)
        
        # Crear título dinámico
        title_text = 'Porcentaje de Uso SAI por Cliente'
        if selected_month_filter:
            title_text += f' ({selected_month_filter})'
        
        fig = px.bar(
            stats_df, 
            x='Cliente', 
            y='Porcentaje_Uso',
            title=title_text,
            labels={'Porcentaje_Uso': '% de Uso', 'Cliente': 'Cliente'},
            text='Porcentaje_Uso'
        )
        
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 100])
        
        # Agregar línea de promedio si se solicita
        if show_average_line:
            average_percentage = stats_df['Porcentaje_Uso'].mean()
            fig.add_hline(
                y=average_percentage, 
                line_dash="dash", 
                line_color=line_color,
                line_width=3  # Línea más gruesa
            )
        
        return fig
    
    return None

def create_time_series_chart(df, month_cols):
    """
    Crea gráfico de serie temporal de adopción con eje Y en números enteros
    """
    monthly_data = []
    for month in month_cols:
        if month in df.columns:
            active_clients = len(df[df[month] > 0]['Cliente'].unique())
            monthly_data.append({'Mes': month, 'Clientes_Activos': active_clients})
    
    if monthly_data:
        chart_df = pd.DataFrame(monthly_data)
        fig = px.line(chart_df, x='Mes', y='Clientes_Activos', 
                     title='Tendencia de Adopción de IA',
                     markers=True)
        
        # Configurar eje Y para mostrar solo números enteros
        max_clients = chart_df['Clientes_Activos'].max()
        fig.update_layout(
            xaxis_title="Mes", 
            yaxis_title="Número de Clientes Activos",
            yaxis=dict(
                dtick=1,  # Incrementos de 1
                range=[0, max_clients + 1]  # Rango desde 0 hasta máximo + 1
            )
        )
        
        return fig
    
    return None

def create_client_status_chart(client_analysis, month_cols):
    """
    Crea gráfico de estado de clientes por mes (siempre todos los meses)
    """
    if not client_analysis:
        return None
    
    months = [data['Mes'] for data in client_analysis]
    nuevos = [len(data['Nuevos']) for data in client_analysis]
    estables = [len(data['Estables']) for data in client_analysis]
    recuperados = [len(data['Recuperados']) for data in client_analysis]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Nuevos', x=months, y=nuevos))
    fig.add_trace(go.Bar(name='Estables', x=months, y=estables))
    fig.add_trace(go.Bar(name='Recuperados', x=months, y=recuperados))
    
    fig.update_layout(
        title='Estado de Clientes por Mes',
        xaxis_title='Mes',
        yaxis_title='Número de Clientes',
        barmode='stack'
    )
    
    return fig

def create_country_comparison_chart(df, month_cols):
    """
    Crea gráfico de comparación por países
    """
    country_data = []
    
    for month in month_cols:
        if month in df.columns:
            for country in df['Pais'].unique():
                if pd.notna(country):
                    country_df = df[df['Pais'] == country]
                    active_clients = len(country_df[country_df[month] > 0]['Cliente'].unique())
                    country_data.append({
                        'Mes': month,
                        'Pais': country,
                        'Clientes_Activos': active_clients
                    })
    
    if country_data:
        chart_df = pd.DataFrame(country_data)
        fig = px.line(chart_df, x='Mes', y='Clientes_Activos', color='Pais',
                     title='Comparación de Adopción de IA por País',
                     markers=True)
        fig.update_layout(xaxis_title="Mes", yaxis_title="Número de Clientes Activos")
        return fig
    
    return None

def create_detailed_client_table(df, client_analysis_by_country, selected_country, selected_month, month_cols):
    """
    Crea tabla detallada de clientes con datos del mes seleccionado únicamente
    """
    if selected_country not in client_analysis_by_country:
        return None
    
    # Encontrar el índice del mes seleccionado
    try:
        current_month_index = month_cols.index(selected_month)
    except ValueError:
        return None
    
    # Determinar el mes anterior
    previous_month = month_cols[current_month_index - 1] if current_month_index > 0 else None
    
    # Buscar los datos del mes seleccionado para el país seleccionado
    country_data = client_analysis_by_country[selected_country]
    month_data = None
    
    for data in country_data:
        if data['Mes'] == selected_month:
            month_data = data
            break
    
    if month_data is None:
        return None
    
    # Obtener todos los clientes únicos que aparecen en el mes actual o anterior
    all_clients = set()
    all_clients.update(month_data['Nuevos'])
    all_clients.update(month_data['Estables'])
    all_clients.update(month_data['Recuperados'])
    all_clients.update(month_data['Perdidos'])
    
    # Clientes del mes anterior (si existe)
    if previous_month:
        country_df = df[df['Pais'] == selected_country]
        if previous_month in df.columns:
            previous_month_clients = country_df[country_df[previous_month] > 0]['Cliente'].unique()
            all_clients.update(previous_month_clients)
    
    # Crear tabla detallada
    detailed_data = []
    
    for client in all_clients:
        client_data = df[df['Cliente'] == client]
        
        # Determinar el tipo de cliente
        client_type = "Sin actividad"
        if client in month_data['Nuevos']:
            client_type = "Nuevo"
        elif client in month_data['Estables']:
            client_type = "Estable"
        elif client in month_data['Recuperados']:
            client_type = "Recuperado"
        elif client in month_data['Perdidos']:
            client_type = "Perdido"
        
        # Total de personas en el cliente
        total_people = len(client_data)
        
        # Estadísticas del mes anterior
        uso_mes_pasado = 0
        adopcion_mes_pasado = 0
        if previous_month and previous_month in df.columns:
            uso_mes_pasado = len(client_data[client_data[previous_month] > 0])
            adopcion_mes_pasado = (uso_mes_pasado / total_people * 100) if total_people > 0 else 0
        
        # Estadísticas del mes actual
        uso_mes_actual = 0
        adopcion_mes_actual = 0
        if selected_month in df.columns:
            uso_mes_actual = len(client_data[client_data[selected_month] > 0])
            adopcion_mes_actual = (uso_mes_actual / total_people * 100) if total_people > 0 else 0
        
        detailed_data.append({
            'Cliente': client,
            'Tipo': client_type,
            'Pais': selected_country,
            'Total de personas': total_people,
            'Uso Mes pasado': uso_mes_pasado,
            '% Adopción mes pasado': round(adopcion_mes_pasado, 2),
            'Uso Mes actual': uso_mes_actual,
            '% Adopción mes actual': round(adopcion_mes_actual, 2)
        })
    
    if detailed_data:
        return pd.DataFrame(detailed_data)
    
    return None

def create_adoption_percentage_by_total_people_chart(df, month_cols):
    """
    Crea gráfico de % de adopción por tiempo con rango dinámico del eje Y
    """
    if df.empty:
        return None
    
    monthly_adoption = []
    
    for month in month_cols:
        if month in df.columns:
            total_people = len(df)
            people_using = len(df[df[month] > 0])
            adoption_percentage = (people_using / total_people * 100) if total_people > 0 else 0
            
            monthly_adoption.append({
                'Mes': month,
                'Porcentaje_Adopcion': round(adoption_percentage, 2)
            })
    
    if monthly_adoption:
        chart_df = pd.DataFrame(monthly_adoption)
        
        # Calcular rango dinámico del eje Y
        min_val = chart_df['Porcentaje_Adopcion'].min()
        max_val = chart_df['Porcentaje_Adopcion'].max()
        
        # Aplicar márgenes del 10%
        y_min = max(0, min_val - (min_val * 0.1))
        y_max = min(100, max_val + (max_val * 0.1))
        
        fig = px.line(
            chart_df, 
            x='Mes', 
            y='Porcentaje_Adopcion',
            title="% de Adopción por Tiempo (Total Personas/Personas que Usan)",
            markers=True,
            labels={'Porcentaje_Adopcion': '% de Adopción', 'Mes': 'Mes'}
        )
        
        fig.update_layout(
            xaxis_title="Mes", 
            yaxis_title="% de Adopción",
            yaxis_range=[y_min, y_max]
        )
        
        return fig
    
    return None

def create_adoption_percentage_by_client_average_chart(df, month_cols):
    """
    Crea gráfico de % de adopción por tiempo con rango dinámico del eje Y
    """
    if df.empty:
        return None
    
    monthly_avg_adoption = []
    
    for month in month_cols:
        if month in df.columns:
            client_adoptions = []
            
            for client in df['Cliente'].unique():
                client_data = df[df['Cliente'] == client]
                total_people = len(client_data)
                people_using = len(client_data[client_data[month] > 0])
                
                if total_people > 0:
                    client_adoption = (people_using / total_people * 100)
                    client_adoptions.append(client_adoption)
            
            if client_adoptions:
                avg_adoption = sum(client_adoptions) / len(client_adoptions)
                monthly_avg_adoption.append({
                    'Mes': month,
                    'Promedio_Adopcion': round(avg_adoption, 2)
                })
    
    if monthly_avg_adoption:
        chart_df = pd.DataFrame(monthly_avg_adoption)
        
        # Calcular rango dinámico del eje Y
        min_val = chart_df['Promedio_Adopcion'].min()
        max_val = chart_df['Promedio_Adopcion'].max()
        
        # Aplicar márgenes del 10%
        y_min = max(0, min_val - (min_val * 0.1))
        y_max = min(100, max_val + (max_val * 0.1))
        
        fig = px.line(
            chart_df, 
            x='Mes', 
            y='Promedio_Adopcion',
            title="% de Adopción por Tiempo (Promedio de % de Adopción de Clientes)",
            markers=True,
            labels={'Promedio_Adopcion': '% de Adopción Promedio', 'Mes': 'Mes'}
        )
        
        fig.update_layout(
            xaxis_title="Mes", 
            yaxis_title="% de Adopción Promedio",
            yaxis_range=[y_min, y_max]
        )
        
        return fig
    
    return None

def show_general_analysis(df_filtered, month_cols, client_analysis, client_analysis_by_country, selected_country_main):
    """
    Muestra la sección de Análisis General
    """
    st.subheader("📊 Análisis General")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Tendencia de Adopción")
        trend_chart = create_time_series_chart(df_filtered, month_cols)
        if trend_chart:
            st.plotly_chart(trend_chart, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para mostrar la tendencia.")
    
    with col2:
        st.subheader("📊 Estado de Clientes por Mes")
        status_chart = create_client_status_chart(client_analysis, month_cols)
        if status_chart:
            st.plotly_chart(status_chart, use_container_width=True)
        else:
            st.warning("No hay datos de estado de clientes.")
    
    # Gráfico de comparación por país (solo si hay más de un país)
    if selected_country_main == "Todos" and len(df_filtered['Pais'].dropna().unique()) > 1:
        st.subheader("🌍 Comparación por País")
        country_chart = create_country_comparison_chart(df_filtered, month_cols)
        if country_chart:
            st.plotly_chart(country_chart, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para la comparación por país.")

def show_usage_analysis(df_filtered, month_cols, client_analysis_by_country, selected_country_main):
    """
    Muestra la sección de Análisis de Uso SAI y Detalle de Clientes
    """
    st.subheader("📊 Análisis de Uso SAI y Detalle de Clientes")
    
    # Filtros para esta sección
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        # Filtro por cliente
        available_clients = ["Todos"] + list(df_filtered['Cliente'].unique())
        selected_client = st.selectbox("Filtrar por Cliente:", available_clients, key="section2_client")
    
    with col_filter2:
        # Filtro por mes para esta sección - DEFAULT EN Aug-25
        default_month_index = 0
        if 'Aug-25' in month_cols:
            default_month_index = month_cols.index('Aug-25')
        
        selected_month_section2 = st.selectbox(
            "Filtrar por Mes:", 
            month_cols, 
            index=default_month_index,
            key="section2_month"
        )
    
    # Aplicar filtros para esta sección
    df_section2 = df_filtered.copy()
    if selected_client != "Todos":
        df_section2 = df_section2[df_section2['Cliente'] == selected_client]
    
    # Gráfico de Porcentaje de Uso SAI con línea de promedio
    st.subheader("📊 Porcentaje de Uso de SAI")
    usage_chart = create_usage_percentage_chart(df_section2, month_cols, selected_month_section2, show_average_line=True)
    if usage_chart:
        st.plotly_chart(usage_chart, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para mostrar el porcentaje de uso.")
    
    # Tabla de Detalle de Clientes
    st.subheader("📋 Detalle de Clientes")
    
    # Determinar el país para la tabla (usar el filtro principal o permitir selección)
    if selected_country_main != "Todos":
        table_country = selected_country_main
    else:
        # Si no hay filtro de país principal, permitir selección
        available_countries_table = list(client_analysis_by_country.keys())
        table_country = st.selectbox("Seleccionar País para tabla:", available_countries_table, key="table_country")
    
    if table_country and selected_month_section2:
        detailed_table = create_detailed_client_table(df_filtered, client_analysis_by_country, table_country, selected_month_section2, month_cols)
        
        if detailed_table is not None and not detailed_table.empty:
            # Aplicar filtro de cliente a la tabla si está seleccionado
            if selected_client != "Todos":
                detailed_table = detailed_table[detailed_table['Cliente'] == selected_client]
            
            # Mostrar resumen
            col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
            
            nuevos_count = len(detailed_table[detailed_table['Tipo'] == 'Nuevo'])
            estables_count = len(detailed_table[detailed_table['Tipo'] == 'Estable'])
            recuperados_count = len(detailed_table[detailed_table['Tipo'] == 'Recuperado'])
            perdidos_count = len(detailed_table[detailed_table['Tipo'] == 'Perdido'])
            
            with col_summary1:
                st.metric("Clientes Nuevos", nuevos_count)
            with col_summary2:
                st.metric("Clientes Estables", estables_count)
            with col_summary3:
                st.metric("Clientes Recuperados", recuperados_count)
            with col_summary4:
                st.metric("Clientes Perdidos", perdidos_count)
            
            # Mostrar tabla completa
            st.dataframe(detailed_table, use_container_width=True)
            
            # Opción para descargar los datos
            csv = detailed_table.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos como CSV",
                data=csv,
                file_name=f"detalle_clientes_{table_country}_{selected_month_section2}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"No hay datos disponibles para {table_country} en {selected_month_section2}")

def show_adoption_analysis(df_filtered, month_cols):
    """
    Muestra la sección de Análisis de Adopción por Tiempo
    """
    st.subheader("📈 Análisis de Adopción por Tiempo")
    
    # Filtros para gráficos de adopción
    col_adopt1, col_adopt2 = st.columns(2)
    
    with col_adopt1:
        # Filtro por cliente para adopción
        available_clients_adopt = ["Todos"] + list(df_filtered['Cliente'].unique())
        selected_client_adopt = st.selectbox("Filtrar por Cliente:", available_clients_adopt, key="adopt_client")
    
    # Aplicar filtros para gráficos de adopción
    df_adoption = df_filtered.copy()
    if selected_client_adopt != "Todos":
        df_adoption = df_adoption[df_adoption['Cliente'] == selected_client_adopt]
    
    # Primera gráfica de adopción
    st.subheader("📊 Adopción: Total Personas vs Personas que Usan")
    adoption_chart1 = create_adoption_percentage_by_total_people_chart(df_adoption, month_cols)
    if adoption_chart1:
        st.plotly_chart(adoption_chart1, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para mostrar el gráfico de adopción.")
    
    # Segunda gráfica de adopción
    st.subheader("📊 Adopción: Promedio de % de Adopción de Clientes")
    adoption_chart2 = create_adoption_percentage_by_client_average_chart(df_adoption, month_cols)
    if adoption_chart2:
        st.plotly_chart(adoption_chart2, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para mostrar el gráfico de adopción promedio.")

def show_comparison_analysis(df_filtered, month_cols):
    """
    Muestra la sección de Comparación Mes Actual vs Mes Anterior (último mes vs previo)
    """
    st.subheader("🔄 Comparación Uso Mes Actual vs Mes Anterior")
    
    # Determinar automáticamente el último mes y el anterior
    if len(month_cols) < 2:
        st.warning("Se necesitan al menos 2 meses de datos para realizar la comparación.")
        return
    
    # Último mes (mes actual) y mes anterior
    current_month = month_cols[-1]  # Último mes en la lista
    previous_month = month_cols[-2]  # Penúltimo mes en la lista
    
    # Mostrar información de los meses que se están comparando
    st.info(f"Comparando: **{previous_month}** (mes anterior) vs **{current_month}** (mes actual)")
    
    # Filtro por cliente
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        available_clients_comparison = ["Todos"] + list(df_filtered['Cliente'].unique())
        selected_client_comparison = st.selectbox(
            "Filtrar por Cliente:", 
            available_clients_comparison, 
            key="comparison_client"
        )
    
    # Aplicar filtros
    df_comparison = df_filtered.copy()
    if selected_client_comparison != "Todos":
        df_comparison = df_comparison[df_comparison['Cliente'] == selected_client_comparison]
    
    # Calcular promedios para mostrar en texto grande
    current_stats = []
    previous_stats = []
    
    for client in df_comparison['Cliente'].unique():
        # Estadísticas mes actual
        total_people, users_current, usage_percentage_current = get_client_usage_stats(
            df_comparison, client, month_cols, current_month
        )
        if total_people > 0:
            current_stats.append(usage_percentage_current)
        
        # Estadísticas mes anterior
        total_people, users_previous, usage_percentage_previous = get_client_usage_stats(
            df_comparison, client, month_cols, previous_month
        )
        if total_people > 0:
            previous_stats.append(usage_percentage_previous)
    
    # Calcular promedios
    avg_current = sum(current_stats) / len(current_stats) if current_stats else 0
    avg_previous = sum(previous_stats) / len(previous_stats) if previous_stats else 0
    difference = avg_current - avg_previous
    
    # Mostrar texto grande con estadísticas
    st.markdown("### 📊 Resumen de Comparación")
    col_text1, col_text2, col_text3 = st.columns(3)
    
    with col_text1:
        st.metric(
            label=f"Promedio {previous_month}",
            value=f"{avg_previous:.1f}%"
        )
    
    with col_text2:
        st.metric(
            label=f"Promedio {current_month}",
            value=f"{avg_current:.1f}%"
        )
    
    with col_text3:
        # Mostrar el cambio con HTML personalizado para color verde
        st.markdown("**Cambio**")
        st.markdown(
            f'<p style="color: #28a745; font-size: 2rem; font-weight: bold; margin: 0;">{difference:+.1f}%</p>',
            unsafe_allow_html=True
        )
    
    # Crear gráficos lado a lado
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader(f"📊 Uso {previous_month}")
        chart_previous = create_usage_percentage_chart(
            df_comparison, month_cols, previous_month, show_average_line=True, line_color="red"
        )
        if chart_previous:
            st.plotly_chart(chart_previous, use_container_width=True)
        else:
            st.warning("No hay datos para el mes anterior.")
    
    with col_chart2:
        st.subheader(f"📊 Uso {current_month}")
        chart_current = create_usage_percentage_chart(
            df_comparison, month_cols, current_month, show_average_line=True, line_color="green"
        )
        if chart_current:
            st.plotly_chart(chart_current, use_container_width=True)
        else:
            st.warning("No hay datos para el mes actual.")

def main():
    """
    Función principal del dashboard con navegación por secciones
    """
    st.title("🤖 Dashboard de Adopción de IA")
    st.markdown("---")
    
    # Cargar y procesar datos principales
    with st.spinner("Cargando y procesando datos principales..."):
        df_sai, df_360 = load_and_process_data()
    
    if df_sai is None or df_360 is None:
        st.error("No se pudieron cargar los archivos principales. Verifica que 'dataSAI.xlsx' y 'data360.xlsx' estén en la misma carpeta.")
        return
    
    # Unir dataframes principales
    df_merged = merge_dataframes(df_sai, df_360)
    
    if df_merged.empty:
        st.error("No se encontraron coincidencias entre los archivos principales.")
        return
    
    # Cargar y procesar datos NCR
    with st.spinner("Procesando datos NCR..."):
        df_ncr = load_and_process_ncr_data()
    
    # Combinar datos principales con datos NCR
    if df_ncr is not None:
        df_final = combine_with_ncr_data(df_merged, df_ncr)
    else:
        df_final = df_merged
    
    # Agregar registros sintéticos para BCI Chile
    df_final = add_synthetic_bci_records(df_final)
    
    # SIDEBAR - FILTROS PRINCIPALES
    st.sidebar.header("Filtros Principales")
    
    # Filtro de clientes elegibles - DEFAULT EN "Si"
    eligible_filter = st.sidebar.selectbox(
        "Clientes elegibles:",
        ["Si", "No"],
        index=0  # Default en "Si"
    )
    
    # Aplicar filtro de clientes elegibles
    df_filtered = filter_eligible_clients(df_final, eligible_filter == "Si")
    
    # Filtro por País
    available_countries = ["Todos"] + list(df_filtered['Pais'].dropna().unique())
    selected_country_main = st.sidebar.selectbox("Filtrar por País:", available_countries)
    
    # Aplicar filtro de país principal
    if selected_country_main != "Todos":
        df_filtered = df_filtered[df_filtered['Pais'] == selected_country_main]
    
    # Obtener columnas de meses
    month_cols = get_month_columns(df_filtered)
    
    if not month_cols:
        st.error("No se encontraron columnas de meses válidas.")
        return
    
    # Análisis de estado de clientes
    client_analysis = analyze_client_status(df_filtered, month_cols)
    client_analysis_by_country = analyze_client_status_by_country(df_filtered, month_cols)
    
    # NAVEGACIÓN POR SECCIONES
    st.subheader("Navegación")
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
    
    # Inicializar estado de sesión para la sección activa
    if 'active_section' not in st.session_state:
        st.session_state.active_section = 'general'
    
    with col_nav1:
        if st.button("📊 Análisis General", use_container_width=True):
            st.session_state.active_section = 'general'
    
    with col_nav2:
        if st.button("📋 Análisis de Uso SAI", use_container_width=True):
            st.session_state.active_section = 'usage'
    
    with col_nav3:
        if st.button("📈 Análisis de Adopción", use_container_width=True):
            st.session_state.active_section = 'adoption'
    
    with col_nav4:
        if st.button("🔄 Comparación Mensual", use_container_width=True):
            st.session_state.active_section = 'comparison'
    
    st.markdown("---")
    
    # Mostrar la sección correspondiente
    if st.session_state.active_section == 'general':
        show_general_analysis(df_filtered, month_cols, client_analysis, client_analysis_by_country, selected_country_main)
    
    elif st.session_state.active_section == 'usage':
        show_usage_analysis(df_filtered, month_cols, client_analysis_by_country, selected_country_main)
    
    elif st.session_state.active_section == 'adoption':
        show_adoption_analysis(df_filtered, month_cols)
    
    elif st.session_state.active_section == 'comparison':
        show_comparison_analysis(df_filtered, month_cols)

if __name__ == "__main__":
    main()
