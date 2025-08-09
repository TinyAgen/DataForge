import streamlit as st
import json
from data_manager import UniversalDataManager, VideoDataManager
from dotenv import load_dotenv
import os


load_dotenv(override=True)
# 页面配置
st.set_page_config(
    page_title="大模型数据生命周期管理系统",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏Streamlit默认的菜单和页面信息
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp > header {display: none;}
.css-1d391kg {display: none;}
[data-testid="stToolbar"] {display: none;}
[data-testid="stDecoration"] {display: none;}
[data-testid="stStatusWidget"] {display: none;}
[data-testid="stHeader"] {display: none;}
.css-18e3th9 {padding-top: 0rem;}
.css-1d391kg {padding-top: 1rem;}

/* 隐藏左上角的页面路径 */
.css-1544g2n {display: none;}
.css-eczf16 {display: none;}
.css-10trblm {display: none;}
.css-1avcm0n {display: none;}
.css-1y4p8pa {display: none;}
[data-testid="stSidebarNav"] {display: none;}
section[data-testid="stSidebar"] .css-ng1t4o {display: none;}
section[data-testid="stSidebar"] .css-1d391kg {display: none;}

/* 隐藏所有可能的导航面包屑 */
/* 注释掉影响所有selectbox的样式 */
/* .stSelectbox > div > div {
    display: none;
} */
div[data-testid="stSidebarNavItems"] {
    display: none;
}
nav[aria-label="Page navigation"] {
    display: none;
}
ul[data-testid="stSidebarNavItems"] {
    display: none;
}

/* 强制隐藏页面名称显示 */
.css-1vq4p4l {display: none !important;}
.css-1544g2n {display: none !important;}
.css-eczf16 {display: none !important;}
.css-10trblm {display: none !important;}
.css-1avcm0n {display: none !important;}

/* 确保侧边栏顶部干净 */
.css-1d391kg {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 初始化数据管理器
@st.cache_resource
def init_manager(project_name=None):
    try:
        # 从环境变量获取API密钥，不再允许用户输入
        print(f"apiKey: {os.getenv('DASHSCOPE_API_KEY')}")
        manager = UniversalDataManager(project_name=project_name, api_key=os.getenv("DASHSCOPE_API_KEY"))
        return manager
    except Exception as e:
        st.error(f"初始化数据管理器失败: {str(e)}")
        return None


# 获取管理器实例
def get_manager():
    # 检查是否有当前项目
    current_project = st.session_state.get("current_project")
    
    # 如果session中有manager且项目匹配，直接返回
    if "manager" in st.session_state:
        manager = st.session_state["manager"]
        if manager.current_project == current_project:
            return manager
    
    # 创建新的manager实例
    manager = init_manager(current_project)
    if manager:
        st.session_state["manager"] = manager
        return manager
    return None

# 侧边栏导航
def sidebar_navigation():
    # 侧边栏样式
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem;">
        <h2 style="color: white; margin: 0;">🧭 导航菜单</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示当前项目状态
    current_project = st.session_state.get("current_project")
    if current_project:
        st.sidebar.markdown(f"""
        <div style="background: #e8f5e8; padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #4CAF50;">
            <h4 style="margin: 0; color: #2e7d32;">📁 当前项目</h4>
            <p style="margin: 0.2rem 0 0 0; color: #1b5e20; font-weight: bold;">{current_project}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div style="background: #fff3e0; padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #ff9800;">
            <h4 style="margin: 0; color: #e65100;">⚠️ 提示</h4>
            <p style="margin: 0.2rem 0 0 0; color: #bf360c;">请先选择项目</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 功能菜单
    st.sidebar.markdown("### 🚀 功能菜单")
    
    # 使用带图标的选项
    menu_options = [
        ("🗂️ 项目管理", "项目管理"),
        ("📊 数据概览", "数据概览"), 
        ("🔍 数据筛选与修改", "数据筛选与修改"),
        ("🤖 数据生成", "数据生成"),
        ("ℹ️ 关于项目", "关于项目")
    ]
    
    # 创建选项字典
    option_dict = {display: value for display, value in menu_options}
    
    page = st.sidebar.radio(
        "选择功能",
        options=list(option_dict.keys()),
        label_visibility="collapsed"
    )
    
    # 返回实际的页面值
    return option_dict[page]


# 数据概览页面
def data_overview_page(manager):
    # 页面标题
    st.markdown("""
    <div style="background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
        <h2 style="color: white; margin: 0; text-align: center;">📊 数据概览</h2>
        <p style="color: #f0f0f0; margin: 0.5rem 0 0 0; text-align: center;">训练数据集和验证数据集的基本信息</p>
    </div>
    """, unsafe_allow_html=True)

    # 数据统计卡片
    col1, col2, col3 = st.columns(3)
    
    train_count = len(manager.train_data)
    val_count = len(manager.val_data)
    total_count = train_count + val_count
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); padding: 1.5rem; border-radius: 15px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin: 0; font-size: 2rem;">🎯</h2>
            <h3 style="color: white; margin: 0.5rem 0;">{train_count}</h3>
            <p style="color: #e3f2fd; margin: 0;">训练数据</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 1.5rem; border-radius: 15px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin: 0; font-size: 2rem;">✅</h2>
            <h3 style="color: white; margin: 0.5rem 0;">{val_count}</h3>
            <p style="color: #fff3e0; margin: 0;">验证数据</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%); padding: 1.5rem; border-radius: 15px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h2 style="color: white; margin: 0; font-size: 2rem;">📈</h2>
            <h3 style="color: white; margin: 0.5rem 0;">{total_count}</h3>
            <p style="color: #f3e5f5; margin: 0;">总数据量</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 数据示例部分
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #2196F3;">
            <h3 style="margin: 0; color: #1976D2;">🎯 训练数据集</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if manager.train_data:
            with st.expander(f"📋 查看训练数据示例 (共{train_count}条)", expanded=False):
                # 默认展示前1条数据
                num_samples = min(1, len(manager.train_data))
                for i in range(num_samples):
                    st.write(f"**示例 {i+1}:**")
                    st.json(manager.train_data[i], expanded=False)
                    if i < num_samples - 1:
                        st.markdown("---")
        else:
            st.info("🚀 暂无训练数据，前往数据生成页面创建数据")

    with col2:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #FF9800;">
            <h3 style="margin: 0; color: #F57C00;">✅ 验证数据集</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if manager.val_data:
            with st.expander(f"📋 查看验证数据示例 (共{val_count}条)", expanded=False):
                # 默认展示前1条数据
                num_samples = min(1, len(manager.val_data))
                for i in range(num_samples):
                    st.write(f"**示例 {i+1}:**")
                    st.json(manager.val_data[i], expanded=False)
                    if i < num_samples - 1:
                        st.markdown("---")
        else:
            st.info("🚀 暂无验证数据，前往数据生成页面创建数据")
    
    # 数据分布图表
    if total_count > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #9C27B0;">
            <h3 style="margin: 0; color: #7B1FA2;">📊 数据分布</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 使用Streamlit的图表功能
        import pandas as pd
        
        chart_data = pd.DataFrame({
            '数据集': ['训练数据', '验证数据'],
            '数量': [train_count, val_count]
        })
        
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.bar_chart(chart_data.set_index('数据集'))
        with col_chart2:
            # 计算百分比
            if total_count > 0:
                train_pct = (train_count / total_count) * 100
                val_pct = (val_count / total_count) * 100
                
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 10px; text-align: center;">
                    <h4>数据分布比例</h4>
                    <p><span style="color: #2196F3;">🎯 训练数据:</span> {train_pct:.1f}%</p>
                    <p><span style="color: #FF9800;">✅ 验证数据:</span> {val_pct:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
# 关于项目页面
def about_page():
    # 页面标题
    st.markdown("""
    <div style="background: linear-gradient(90deg, #673AB7 0%, #9C27B0 100%); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
        <h2 style="color: white; margin: 0; text-align: center;">ℹ️ 关于项目</h2>
        <p style="color: #f0f0f0; margin: 0.5rem 0 0 0; text-align: center;">大模型数据生命周期管理系统 - 助力AI数据管理</p>
    </div>
    """, unsafe_allow_html=True)

    # 核心功能卡片
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #4CAF50; margin-bottom: 1.5rem;">
        <h3 style="margin: 0; color: #2e7d32;">🚀 核心功能</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="color: #1976D2; margin-top: 0;">🗂️ 项目管理</h4>
            <p style="margin-bottom: 0;">创建和管理多个独立的数据项目，支持自定义Schema</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="color: #FF9800; margin-top: 0;">🔍 数据过滤</h4>
            <p style="margin-bottom: 0;">通过标签、正则表达式和大模型语义进行智能过滤</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="color: #9C27B0; margin-top: 0;">✏️ 数据修改</h4>
            <p style="margin-bottom: 0;">查找并修改特定数据条目，支持批量编辑</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="color: #4CAF50; margin-top: 0;">🤖 数据生成</h4>
            <p style="margin-bottom: 0;">通过大模型自动生成新数据，支持多种生成模式</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="color: #F44336; margin-top: 0;">💾 数据保存</h4>
            <p style="margin-bottom: 0;">灵活保存到训练集或验证集，支持实时预览</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="color: #795548; margin-top: 0;">📊 数据分析</h4>
            <p style="margin-bottom: 0;">直观的数据统计和分布可视化</p>
        </div>
        """, unsafe_allow_html=True)

    # 使用说明
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #2196F3; margin: 2rem 0 1.5rem 0;">
        <h3 style="margin: 0; color: #1976D2;">📖 使用说明</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <ol style="margin: 0; padding-left: 1.5rem;">
            <li style="margin-bottom: 0.5rem;"><strong>安装依赖:</strong> <code>pip install -r requirements.txt</code></li>
            <li style="margin-bottom: 0.5rem;"><strong>运行应用:</strong> <code>streamlit run main.py</code></li>
            <li style="margin-bottom: 0.5rem;"><strong>创建项目:</strong> 首先在项目管理页面创建或选择项目</li>
            <li style="margin-bottom: 0;"><strong>开始工作:</strong> 使用各功能页面进行数据管理</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # 项目结构
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #FF9800; margin: 2rem 0 1.5rem 0;">
        <h3 style="margin: 0; color: #F57C00;">🏗️ 项目结构</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.code("""
data/
├── project_name/
│   ├── train_data.json      # 训练数据
│   ├── val_data.json        # 验证数据
│   ├── config.json          # 项目配置(Schema等)
│   └── system_prompts/      # 系统提示词目录
└── video_agent/             # 示例项目
    ├── train_data.json
    ├── val_data.json
    ├── config.json
    └── system_prompts/
    """, language="text")

    # 注意事项
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #F44336; margin: 2rem 0 1.5rem 0;">
        <h3 style="margin: 0; color: #D32F2F;">⚠️ 注意事项</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <ul style="margin: 0; padding-left: 1.5rem;">
            <li style="margin-bottom: 0.5rem;">生成新数据时，建议先少量测试以验证模型效果</li>
            <li style="margin-bottom: 0.5rem;">修改数据前最好备份原始数据文件</li>
            <li style="margin-bottom: 0.5rem;">每个项目都有独立的配置和数据管理</li>
            <li style="margin-bottom: 0;">使用大模型功能需要有效的API密钥</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 版本信息
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: #f0f0f0; border-radius: 10px;">
        <p style="margin: 0; color: #666;">🤖 大模型Agent数据生命周期管理系统 v1.0.0</p>
        <p style="margin: 0; color: #999; font-size: 0.9rem;">Powered by Streamlit & Python</p>
    </div>
    """, unsafe_allow_html=True)

# 主函数
def main():
    # 创建漂亮的标题头部
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">🤖 大模型Agent数据生命周期管理系统</h1>
        <p style="color: #f0f0f0; margin: 0.5rem 0 0 0; font-size: 1.1rem;">AI Data Lifecycle Management Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 侧边栏导航
    page = sidebar_navigation()
    
    # 获取数据管理器
    manager = get_manager()
    
    # 根据选择的页面显示内容
    if page == "项目管理":
        from pages.project_management import project_management_page
        project_management_page(manager)
    elif page == "数据概览":
        if manager and manager.current_project:
            data_overview_page(manager)
        else:
            st.warning("请先在项目管理页面选择或创建一个项目")
    elif page == "数据筛选与修改":
        if manager and manager.current_project:
            from pages.data_filter_modify import data_filter_modify_page
            data_filter_modify_page(manager)
        else:
            st.warning("请先在项目管理页面选择或创建一个项目")
    elif page == "数据生成":
        if manager and manager.current_project:
            from pages.data_generation import data_generation_page
            data_generation_page(manager)
        else:
            st.warning("请先在项目管理页面选择或创建一个项目")
    elif page == "关于项目":
        about_page()

if __name__ == "__main__":
    main()