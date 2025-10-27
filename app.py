import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# アプリの表示設定をワイドに設定
st.set_page_config(layout="wide") 

# --- 1. 関数定義: データの読み込み、集計、グラフ描画、データ追加・削除 ---

def load_data():
    """CSVを読み込み、日付型に変換して返す関数"""
    try:
        df = pd.read_csv('data/activity_log.csv')
        
        # 日付形式を柔軟に推測・変換
        df['Date'] = pd.to_datetime(df['Date'], format='mixed')
        
        return df
    except FileNotFoundError:
        st.error("エラー: 'data/activity_log.csv' ファイルが見つかりません。")
        st.stop()
    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")
        st.stop()

def get_time_summary(df_filtered):
    """フィルタリングされたデータでカテゴリ別合計時間を集計する関数"""
    if df_filtered.empty or df_filtered['Hours'].sum() == 0:
        return pd.DataFrame(), 0
        
    time_summary = df_filtered.groupby('Category')['Hours'].sum().reset_index()
    time_summary.columns = ['活動カテゴリ', '合計時間 (H)']
    total_hours = time_summary['合計時間 (H)'].sum()
    return time_summary, total_hours

def create_pie_chart(time_summary, title_text):
    """Plotlyの円グラフを作成・調整する関数"""
    fig = px.pie(
        time_summary,
        values='合計時間 (H)',
        names='活動カテゴリ',
        title=f'**{title_text}**',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.D3
    )
    
    fig.update_layout(
        font=dict(size=14),
        title_x=0.5,
        title_y=0.9,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def create_line_chart(df_data, title_text):
    """週次活動時間の折れ線グラフを作成する関数"""
    df_weekly = df_data.set_index('Date')['Hours'].resample('W').sum().reset_index()
    df_weekly.columns = ['日付', '合計時間 (H)']
    
    fig_line = px.line(
        df_weekly, 
        x='日付', 
        y='合計時間 (H)', 
        title=f'**{title_text}**'
    )
    
    fig_line.update_traces(mode='lines+markers')
    fig_line.update_yaxes(title='合計時間 (H)', rangemode='tozero')
    fig_line.update_xaxes(title='日付', showgrid=True)
    
    return fig_line

def add_new_activity_form():
    """新しい活動を入力し、CSVに書き込むフォームをサイドバーに表示する関数"""
    
    st.sidebar.header('➕ 新しい活動を追加')
    
    with st.sidebar.form("new_activity_form", clear_on_submit=True):
        st.subheader("活動内容を入力")
        
        new_date = st.date_input("日付", value=datetime.now().date())
        categories = ['企業研究', 'ES作成', '面接対策', 'ポートフォリオ', 'その他']
        new_category = st.selectbox("カテゴリ", categories)
        new_hours = st.number_input("時間 (H)", min_value=0.1, max_value=24.0, step=0.5, value=1.0)
        
        submitted = st.form_submit_button("データ追加")

        if submitted:
            try:
                df = pd.read_csv('data/activity_log.csv')
            except:
                st.error("CSVファイルの読み込みエラー。")
                return

            new_data = pd.DataFrame([{
                'Date': new_date.strftime('%Y-%m-%d'),
                'Category': new_category,
                'Hours': new_hours
            }])
            
            updated_df = pd.concat([df, new_data], ignore_index=True)
            
            updated_df.to_csv('data/activity_log.csv', index=False)
            
            st.success(f"データ ({new_category}: {new_hours}H) を追加し、CSVを更新しました！")
            
            # 自動更新のトリガー
            st.rerun() 

# --- 2. メイン処理 ---

st.title('🎯 就活活動時間 分析ダッシュボード')
st.caption('PandasとStreamlitを用いて、活動時間を期間別に可視化・データ管理しています。')

# データ入力フォームをサイドバーに配置
add_new_activity_form()

# データのロード
df = load_data()
df = df.sort_values('Date', ascending=False) 

# 期間設定
today = pd.to_datetime(datetime.now().date())
date_ranges = {
    "直近7日": today - timedelta(days=7),
    "直近30日": today - timedelta(days=30),
    "直近5ヶ月": today - timedelta(days=5 * 30),
    "全期間": df['Date'].min() 
}

# Streamlitのタブ機能でコンテンツを整理
tab_names = list(date_ranges.keys()) + ["活動推移", "生データ"]
tabs = st.tabs(tab_names)

# --- 期間別分析タブ (円グラフと集計表) ---
for i, (tab_name, start_date) in enumerate(date_ranges.items()):
    with tabs[i]:
        st.header(f'📅 {tab_name} の活動分析')
        
        if tab_name == "全期間":
            df_filtered = df.copy()
        else:
            df_filtered = df[df['Date'] >= start_date].copy()
        
        time_summary, total_hours = get_time_summary(df_filtered)
        
        st.metric(label="合計活動時間", value=f"{total_hours:.1f} 時間", delta="この期間に費やした合計時間")
        st.markdown("---")

        if time_summary.empty:
            st.warning("この期間の活動データはありません。")
        else:
            col_chart, col_table = st.columns([2, 1])
            
            with col_chart:
                fig = create_pie_chart(time_summary, f'{tab_name}のカテゴリ別内訳')
                st.plotly_chart(fig, use_container_width=True)

            with col_table:
                st.subheader(f'カテゴリ別時間 (H)')
                st.dataframe(time_summary, use_container_width=True, hide_index=True)


# --- 活動推移タブ (折れ線グラフ) ---
with tabs[len(date_ranges)]:
    st.header('📈 週次活動時間の推移')
    if df.empty:
         st.warning("データがありません。サイドバーから活動を追加してください。")
    else:
        fig_line = create_line_chart(df, '週間活動時間の推移')
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption('※週次の合計時間を示しています。')

# --- 生データ確認タブ (削除機能付き) ---
with tabs[len(date_ranges) + 1]:
    st.header('📑 活動ログデータ (全件)')
    
    if df.empty:
        st.info("データがありません。サイドバーから活動を追加してください。")
    else:
        # ユーザーに分かりやすいように、一時的に連番のIndex列を付与して表示
        df_display = df.reset_index(drop=True)
        # DataFrameのIndex (0, 1, 2...) を表示させる
        df_display.index.name = 'Index' 
        st.dataframe(df_display, use_container_width=True)

        st.markdown("---")
        st.subheader("🗑️ データ削除")
        
        # 削除フォーム
        with st.form("delete_form", clear_on_submit=True):
            # ユーザーに削除したい行のIndex番号を選んでもらう
            # Indexは0から始まる連番です
            indices_to_delete = st.multiselect(
                "削除したい行のIndex番号を選択してください (一番左の列)",
                options=df_display.index.tolist(),
                default=[]
            )
            
            delete_submitted = st.form_submit_button("選択したデータを削除")
            
            if delete_submitted:
                if not indices_to_delete:
                    st.warning("削除する行が選択されていません。")
                else:
                    # 削除処理
                    
                    # 1. 選択されたIndexを使ってDataFrameから行を削除
                    # drop(index, axis=0) で指定したインデックスの行を削除
                    df_final = df.drop(indices_to_delete, axis=0) 
                    
                    # 2. CSVファイルに上書き保存 (データ永続化)
                    df_final.to_csv('data/activity_log.csv', index=False)
                    
                    st.success(f"✅ {len(indices_to_delete)} 件のデータを削除し、CSVを更新しました！")
                    
                    # 3. グラフや表に反映させるためにアプリをリロード
                    st.rerun()