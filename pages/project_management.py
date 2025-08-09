import streamlit as st
import json
import os
import shutil
from pathlib import Path

# 项目管理页面
def project_management_page(manager):
    st.title("项目管理")
    
    # 获取现有项目列表
    existing_projects = manager.list_projects()
    
    # 初始化页面状态
    if "pm_page_state" not in st.session_state:
        st.session_state["pm_page_state"] = "overview"
    
    # 页面状态管理
    page_state = st.session_state["pm_page_state"]
    
    if page_state == "overview":
        show_project_overview(manager, existing_projects)
    elif page_state == "create":
        show_create_project_page(manager)
    elif page_state == "edit":
        show_edit_project_page(manager, existing_projects)

def show_project_overview(manager, existing_projects):
    """显示项目概览页面"""
    st.write("管理您的数据项目，查看项目统计信息")
    
    # 操作按钮
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("➕ 创建新项目", use_container_width=True):
            st.session_state["pm_page_state"] = "create"
            st.rerun()
    
    with col2:
        if existing_projects:
            if st.button("✏️ 修改项目", use_container_width=True):
                st.session_state["pm_page_state"] = "edit"
                st.rerun()
        else:
            st.button("✏️ 修改项目", disabled=True, use_container_width=True, help="暂无项目可修改")
    
    st.markdown("---")
    
    if existing_projects:
        st.subheader(f"项目概览 ({len(existing_projects)}个项目)")
        
        # 显示项目卡片
        for i, project_name in enumerate(existing_projects):
            try:
                # 创建临时管理器来读取项目信息
                temp_manager = manager.__class__(project_name=project_name, api_key=manager.api_key)
                
                # 项目卡片
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 2])
                    
                    with col1:
                        is_current = manager.current_project == project_name
                        if is_current:
                            st.markdown(f"**🎯 {project_name}** *(当前项目)*")
                        else:
                            st.markdown(f"**📁 {project_name}**")
                    
                    with col2:
                        st.metric("训练数据", len(temp_manager.train_data))
                    
                    with col3:
                        st.metric("验证数据", len(temp_manager.val_data))
                    
                    with col4:
                        total_data = len(temp_manager.train_data) + len(temp_manager.val_data)
                        st.metric("总计", total_data)
                    
                    with col5:
                        col5_1, col5_2 = st.columns(2)
                        with col5_1:
                            if not is_current:
                                if st.button("选择", key=f"select_{project_name}"):
                                    try:
                                        manager.set_project(project_name)
                                        st.session_state["current_project"] = project_name
                                        st.session_state["manager"] = manager
                                        st.success(f"已切换到项目: {project_name}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"切换项目失败: {str(e)}")
                            else:
                                st.success("✓ 当前")
                        
                        with col5_2:
                            if st.button("🗑️", key=f"delete_{project_name}", help="删除项目"):
                                st.session_state[f"confirm_delete_{project_name}"] = True
                                st.rerun()
                    
                    # 删除确认对话框
                    if st.session_state.get(f"confirm_delete_{project_name}", False):
                        st.warning(f"⚠️ 确认删除项目 '{project_name}' 吗？此操作不可撤销！")
                        col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 1, 4])
                        with col_confirm1:
                            if st.button("确认删除", key=f"confirm_del_{project_name}", type="primary"):
                                try:
                                    manager.delete_project(project_name)
                                    if st.session_state.get("current_project") == project_name:
                                        if "current_project" in st.session_state:
                                            del st.session_state["current_project"]
                                        # 重新初始化manager
                                        st.session_state["manager"] = manager.__class__(api_key=manager.api_key)
                                    st.success(f"项目 '{project_name}' 已删除")
                                    del st.session_state[f"confirm_delete_{project_name}"]
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"删除项目失败: {str(e)}")
                        with col_confirm2:
                            if st.button("取消", key=f"cancel_del_{project_name}"):
                                del st.session_state[f"confirm_delete_{project_name}"]
                                st.rerun()
                    
                    # 项目详情展开
                    with st.expander(f"📋 {project_name} 详情"):
                        detail_col1, detail_col2 = st.columns(2)
                        with detail_col1:
                            st.write("**Input Schema:**")
                            st.json(temp_manager.input_schema, expanded=False)
                        with detail_col2:
                            st.write("**Result Schema:**")
                            st.json(temp_manager.result_schema, expanded=False)
                
                if i < len(existing_projects) - 1:
                    st.markdown("---")
                    
            except Exception as e:
                st.error(f"无法读取项目 '{project_name}' 的信息: {str(e)}")
    else:
        st.info("🚀 还没有任何项目，点击上方'创建新项目'开始使用！")
        
        # 检查是否有旧数据需要迁移
        old_data_path = os.path.join("data", "train_data.json")
        if os.path.exists(old_data_path):
            st.markdown("---")
            st.warning("💡 检测到旧版本数据，是否迁移到新项目？")
            if st.button("🔄 自动迁移到 'video_agent' 项目"):
                try:
                    # 创建video_agent项目
                    default_input_schema = {
                        "type": "object",
                        "properties": {
                            "history": {"type": "array"},
                            "query": {"type": "string"},
                            "env": {"type": "string"},
                            "search_results": {"type": "string"}
                        }
                    }
                    default_result_schema = {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "turn": {"type": "integer"},
                            "query_independent": {"type": "boolean"},
                            "target": {"type": "string"},
                            "processed_query": {"type": "string"},
                            "search": {"type": "boolean"}
                        }
                    }
                    
                    manager.create_project("video_agent", default_input_schema, default_result_schema)
                    
                    # 复制数据文件
                    project_dir = os.path.join(manager.projects_root, "video_agent")
                    shutil.copy2(old_data_path, os.path.join(project_dir, "train_data.json"))
                    
                    val_data_path = os.path.join("data", "val_data.json")
                    if os.path.exists(val_data_path):
                        shutil.copy2(val_data_path, os.path.join(project_dir, "val_data.json"))
                    
                    # 复制system_prompts目录
                    old_prompts_dir = "system_prompts"
                    if os.path.exists(old_prompts_dir):
                        new_prompts_dir = os.path.join(project_dir, "system_prompts")
                        if os.path.exists(new_prompts_dir):
                            shutil.rmtree(new_prompts_dir)
                        shutil.copytree(old_prompts_dir, new_prompts_dir)
                    
                    st.success("✅ 数据已成功迁移到 'video_agent' 项目")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"迁移数据时出错: {str(e)}")

def show_create_project_page(manager):
    """显示创建项目页面"""
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← 返回", use_container_width=True):
            st.session_state["pm_page_state"] = "overview"
            st.rerun()
    
    st.subheader("创建新项目")
    
    # 项目创建表单
    with st.form("create_project_form"):
        new_project_name = st.text_input("项目名称", placeholder="请输入项目名称")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Input JSON Schema**")
            input_schema_text = st.text_area(
                "定义Input数据结构", 
                height=300, 
                value="""{
  "type": "object",
  "properties": {
    "history": {"type": "array"},
    "query": {"type": "string"},
    "env": {"type": "string"},
    "search_results": {"type": "string"}
  },
  "required": ["query"]
}""",
                help="定义输入数据的JSON Schema格式"
            )
        
        with col2:
            st.write("**Result JSON Schema**")
            result_schema_text = st.text_area(
                "定义Result数据结构", 
                height=300, 
                value="""{
  "type": "object",
  "properties": {
    "id": {"type": "integer"},
    "turn": {"type": "integer"},
    "query_independent": {"type": "boolean"},
    "target": {"type": "string"},
    "processed_query": {"type": "string"},
    "search": {"type": "boolean"}
  },
  "required": ["id", "processed_query"]
}""",
                help="定义输出结果的JSON Schema格式"
            )
        
        # 表单提交按钮
        submitted = st.form_submit_button("创建项目", use_container_width=True, type="primary")
        
        if submitted:
            if new_project_name and input_schema_text and result_schema_text:
                # 验证项目名称
                if not new_project_name.strip():
                    st.error("❌ 项目名称不能为空")
                    return
                
                # 分别验证两个Schema
                input_schema = None
                result_schema = None
                validation_errors = []
                
                # 验证Input Schema
                try:
                    input_schema = json.loads(input_schema_text)
                except json.JSONDecodeError as e:
                    error_line = getattr(e, 'lineno', '未知')
                    error_col = getattr(e, 'colno', '未知')
                    validation_errors.append(f"**Input Schema** 格式错误：\n- 位置：第 {error_line} 行，第 {error_col} 列\n- 错误：{e.msg}")
                
                # 验证Result Schema
                try:
                    result_schema = json.loads(result_schema_text)
                except json.JSONDecodeError as e:
                    error_line = getattr(e, 'lineno', '未知')
                    error_col = getattr(e, 'colno', '未知')
                    validation_errors.append(f"**Result Schema** 格式错误：\n- 位置：第 {error_line} 行，第 {error_col} 列\n- 错误：{e.msg}")
                
                # 如果有验证错误，显示详细信息
                if validation_errors:
                    st.error("❌ Schema验证失败：")
                    for error in validation_errors:
                        st.markdown(error)
                    
                    # 提供常见错误提示
                    with st.expander("💡 常见JSON格式错误提示"):
                        st.markdown("""
                        **常见错误及解决方法：**
                        - **缺少逗号**：对象属性之间需要用逗号分隔
                        - **多余逗号**：最后一个属性后不能有逗号
                        - **引号不匹配**：字符串必须用双引号包围
                        - **括号不匹配**：检查 `{` `}` `[` `]` 是否配对
                        - **属性名未加引号**：JSON中属性名必须用双引号
                        
                        **正确格式示例：**
                        ```json
                        {
                          "type": "object",
                          "properties": {
                            "field1": {"type": "string"},
                            "field2": {"type": "integer"}
                          }
                        }
                        ```
                        """)
                    return
                
                # Schema验证通过，创建项目
                try:
                    manager.create_project(new_project_name, input_schema, result_schema)
                    st.success(f"✅ 项目 '{new_project_name}' 创建成功")
                    st.session_state["pm_page_state"] = "overview"
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ 项目创建失败: {str(e)}")
                except Exception as e:
                    st.error(f"❌ 创建项目时出错: {str(e)}")
            else:
                st.error("❌ 请填写所有必要信息")

def show_edit_project_page(manager, existing_projects):
    """显示编辑项目页面"""
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← 返回", use_container_width=True):
            st.session_state["pm_page_state"] = "overview"
            st.rerun()
    
    st.subheader("修改项目")
    
    if not existing_projects:
        st.warning("没有可编辑的项目")
        return
    
    # 选择要编辑的项目
    selected_project = st.selectbox("选择要编辑的项目", existing_projects)
    
    if selected_project:
        try:
            # 加载项目信息
            temp_manager = manager.__class__(project_name=selected_project, api_key=manager.api_key)
            
            # 显示项目基本信息
            st.info(f"正在编辑项目: **{selected_project}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("训练数据", len(temp_manager.train_data))
            with col2:
                st.metric("验证数据", len(temp_manager.val_data))
            with col3:
                total_data = len(temp_manager.train_data) + len(temp_manager.val_data)
                st.metric("总数据量", total_data)
            
            # Schema编辑表单
            with st.form("edit_project_form"):
                st.write("### 编辑项目Schema")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Input JSON Schema**")
                    new_input_schema_text = st.text_area(
                        "Input Schema", 
                        value=json.dumps(temp_manager.input_schema, ensure_ascii=False, indent=2),
                        height=300
                    )
                
                with col2:
                    st.write("**Result JSON Schema**")
                    new_result_schema_text = st.text_area(
                        "Result Schema", 
                        value=json.dumps(temp_manager.result_schema, ensure_ascii=False, indent=2),
                        height=300
                    )
                
                # 表单提交按钮
                col_save, col_load = st.columns([1, 1])
                with col_save:
                    save_submitted = st.form_submit_button("💾 保存配置", use_container_width=True, type="primary")
                with col_load:
                    load_submitted = st.form_submit_button("🔄 加载到当前", use_container_width=True)
                
                if save_submitted:
                    # 分别验证两个Schema
                    input_schema = None
                    result_schema = None
                    validation_errors = []
                    
                    # 验证Input Schema
                    try:
                        input_schema = json.loads(new_input_schema_text)
                    except json.JSONDecodeError as e:
                        error_line = getattr(e, 'lineno', '未知')
                        error_col = getattr(e, 'colno', '未知')
                        validation_errors.append(f"**Input Schema** 格式错误：\n- 位置：第 {error_line} 行，第 {error_col} 列\n- 错误：{e.msg}")
                    
                    # 验证Result Schema
                    try:
                        result_schema = json.loads(new_result_schema_text)
                    except json.JSONDecodeError as e:
                        error_line = getattr(e, 'lineno', '未知')
                        error_col = getattr(e, 'colno', '未知')
                        validation_errors.append(f"**Result Schema** 格式错误：\n- 位置：第 {error_line} 行，第 {error_col} 列\n- 错误：{e.msg}")
                    
                    # 如果有验证错误，显示详细信息
                    if validation_errors:
                        st.error("❌ Schema验证失败：")
                        for error in validation_errors:
                            st.markdown(error)
                        return
                    
                    # Schema验证通过，保存配置
                    try:
                        temp_manager.save_project_config(input_schema, result_schema)
                        st.success(f"✅ 项目 '{selected_project}' 配置已保存")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 保存配置时出错: {str(e)}")
                
                if load_submitted:
                    try:
                        # 切换到选中的项目
                        manager.set_project(selected_project)
                        st.session_state["current_project"] = selected_project
                        st.session_state["manager"] = manager
                        st.success(f"✅ 已切换到项目: {selected_project}")
                        st.session_state["pm_page_state"] = "overview"
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 切换项目失败: {str(e)}")
                        
        except Exception as e:
            st.error(f"❌ 无法加载项目信息: {str(e)}")