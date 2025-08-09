import streamlit as st
import json


# 数据筛选与修改页面
def data_filter_modify_page(manager):
    st.title("数据筛选与修改")
    st.write("筛选数据并修改选中的条目")

    # 数据筛选部分
    st.subheader("数据筛选")
    filter_type = st.selectbox(
        "过滤方式",
        ["标签过滤", "正则表达式过滤", "大模型语义过滤", "组合过滤"],
        key="main_filter_type"
    )

    data_type = st.radio(
        "选择数据集",
        ["训练数据集", "验证数据集"],
        horizontal=True,
        key="main_data_type"
    )
    data_type = "train" if data_type == "训练数据集" else "val"

    if filter_type == "标签过滤":
        tags_input = st.text_input("输入标签(用逗号分隔)", key="tags_filter_input")
        if tags_input:
            tags = [tag.strip() for tag in tags_input.split(",")]
            if st.button("应用过滤", key="apply_tags_filter"):
                filtered_data = manager.filter_by_tags(data_type=data_type, tags=tags)
                st.session_state["filtered_data"] = filtered_data
                st.write(f"过滤结果: {len(filtered_data)} 条数据")
                if filtered_data:
                    # 使用数据管理器的通用显示方法
                    display_data = []
                    for item in filtered_data:
                        info = manager.get_item_display_info(item)
                        display_data.append({
                            "ID": info["id"],
                            "查询内容": info["query"],
                            "详细信息": info["main_text"][:100] + "..." if len(info["main_text"]) > 100 else info["main_text"]
                        })
                    st.dataframe(display_data)

    elif filter_type == "正则表达式过滤":
        pattern = st.text_input("输入正则表达式", key="regex_filter_input")
        if pattern:
            if st.button("应用过滤", key="apply_regex_filter"):
                filtered_data = manager.filter_by_regex(data_type=data_type, pattern=pattern)
                st.session_state["filtered_data"] = filtered_data
                st.write(f"过滤结果: {len(filtered_data)} 条数据")
                if filtered_data:
                    # 使用数据管理器的通用显示方法
                    display_data = []
                    for item in filtered_data:
                        info = manager.get_item_display_info(item)
                        display_data.append({
                            "ID": info["id"],
                            "查询内容": info["query"],
                            "详细信息": info["main_text"][:100] + "..." if len(info["main_text"]) > 100 else info["main_text"]
                        })
                    st.dataframe(display_data)

    elif filter_type == "大模型语义过滤":
        query = st.text_input("输入语义查询", key="semantic_filter_input")
        model = st.selectbox(
            "选择模型",
            ["qwen-max", "qwen-turbo", "qwen-plus"],
            index=0,
            key="semantic_filter_model"
        )
        if query:
            if st.button("应用过滤", key="apply_semantic_filter"):
                # 创建进度条和状态文本
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    model_info = st.empty()
                    model_info.info(f"当前使用模型: {model}")

                    # 定义回调函数
                    def update_progress(message, progress):
                        status_text.info(message)
                        progress_bar.progress(progress)
                        # 在回调中更新模型信息
                        model_info.info(f"当前使用模型: {model}")

                    try:
                        status_text.info(f"开始使用{model}模型进行语义过滤...")
                        filtered_data = manager.filter_by_llm(
                            data_type=data_type,
                            query=query,
                            callback=update_progress,
                            model=model
                        )
                        st.session_state["filtered_data"] = filtered_data
                        st.write(f"过滤结果: {len(filtered_data)} 条数据")
                        if filtered_data:
                            # 使用数据管理器的通用显示方法
                            display_data = []
                            for item in filtered_data:
                                info = manager.get_item_display_info(item)
                                display_data.append({
                                    "ID": info["id"],
                                    "查询内容": info["query"],
                                    "详细信息": info["main_text"][:100] + "..." if len(info["main_text"]) > 100 else info["main_text"]
                                })
                            st.dataframe(display_data)
                        # 完成后清除状态
                        status_text.success("语义过滤完成")
                    except Exception as e:
                        st.error(f"语义过滤失败: {str(e)}")
                        # 出错时清除状态
                        status_text.error(f"过滤出错: {str(e)}")

    elif filter_type == "组合过滤":
        st.write("配置多个过滤步骤，将按顺序应用")

        # 初始化过滤步骤列表
        if "filter_steps" not in st.session_state:
            st.session_state["filter_steps"] = []

        # 添加新过滤步骤
        col1, col2 = st.columns([2, 1])
        with col1:
            new_filter_type = st.selectbox(
                "添加过滤步骤",
                ["标签过滤", "正则表达式过滤", "大模型语义过滤"],
                key="new_filter_type"
            )
        with col2:
            if st.button("添加步骤", key="add_filter_step"):
                step_id = len(st.session_state["filter_steps"]) + 1
                st.session_state["filter_steps"].append({
                    "id": step_id,
                    "type": new_filter_type,
                    "params": {}
                })
                st.rerun()

        # 显示和配置过滤步骤
        if st.session_state["filter_steps"]:
            st.write("### 过滤步骤配置")
            for idx, step in enumerate(st.session_state["filter_steps"]):
                with st.expander(f"步骤 {step['id']}: {step['type']}"):
                    if step['type'] == "标签过滤":
                        tags_input = st.text_input(
                            "输入标签(用逗号分隔)",
                            key=f"tags_{step['id']}"
                        )
                        if tags_input:
                            step['params']['tags'] = [tag.strip() for tag in tags_input.split(",")]

                    elif step['type'] == "正则表达式过滤":
                        pattern = st.text_input(
                            "输入正则表达式",
                            key=f"pattern_{step['id']}"
                        )
                        if pattern:
                            step['params']['pattern'] = pattern

                    elif step['type'] == "大模型语义过滤":
                        query = st.text_input(
                            "输入语义查询",
                            key=f"llm_query_{step['id']}"
                        )
                        model = st.selectbox(
                            "选择模型",
                            ["qwen-max", "qwen-turbo", "qwen-plus"],
                            index=0,
                            key=f"llm_model_{step['id']}"
                        )
                        if query:
                            step['params']['query'] = query
                            step['params']['model'] = model

                    # 删除按钮
                    if st.button("删除此步骤", key=f"delete_{step['id']}"):
                        st.session_state["filter_steps"].pop(idx)
                        st.rerun()

            # 应用组合过滤
            if st.button("应用组合过滤", key="apply_combined_filter"):
                # 检查是否所有必要参数都已设置
                valid = True
                for step in st.session_state["filter_steps"]:
                    if step['type'] == "标签过滤" and ('tags' not in step['params'] or not step['params']['tags']):
                        st.warning("请设置所有标签过滤步骤的标签")
                        valid = False
                        break
                    elif step['type'] == "正则表达式过滤" and ('pattern' not in step['params'] or not step['params']['pattern']):
                        st.warning("请设置所有正则表达式过滤步骤的模式")
                        valid = False
                        break
                    elif step['type'] == "大模型语义过滤" and ('query' not in step['params'] or not step['params']['query']):
                        st.warning("请设置所有大模型语义过滤步骤的查询")
                        valid = False
                        break

                if valid:
                    # 构建过滤配置
                    filters = []
                    for step in st.session_state["filter_steps"]:
                        filter_type_map = {
                            "标签过滤": "tags",
                            "正则表达式过滤": "regex",
                            "大模型语义过滤": "llm"
                        }
                        filters.append({
                            "type": filter_type_map[step['type']],
                            "params": step['params']
                        })

                    # 创建进度条和状态文本
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("准备开始组合过滤...")

                    # 定义进度回调函数
                    def update_progress(message, progress):
                        progress_bar.progress(progress)
                        status_text.text(message)

                    try:
                        filtered_data = manager.filter_combined(
                            data_type=data_type,
                            filters=filters,
                            callback=update_progress
                        )
                        st.session_state["filtered_data"] = filtered_data
                        status_text.success(f"组合过滤完成，找到 {len(filtered_data)} 条数据")
                        st.write(f"组合过滤结果: {len(filtered_data)} 条数据")
                        if filtered_data:
                            # 使用数据管理器的通用显示方法
                            display_data = []
                            for item in filtered_data:
                                info = manager.get_item_display_info(item)
                                display_data.append({
                                    "ID": info["id"],
                                    "查询内容": info["query"],
                                    "详细信息": info["main_text"][:100] + "..." if len(info["main_text"]) > 100 else info["main_text"]
                                })
                            st.dataframe(display_data)
                    except Exception as e:
                        status_text.error(f"组合过滤失败: {str(e)}")
                        st.error(f"组合过滤失败: {str(e)}")
        else:
            st.info("请添加过滤步骤")

    # 数据修改部分
    if "filtered_data" in st.session_state and st.session_state["filtered_data"]:
        st.subheader("数据修改")
        if len(st.session_state["filtered_data"]) > 0:
            def format_item(i):
                item = st.session_state['filtered_data'][i]
                info = manager.get_item_display_info(item)
                return f"ID: {info['id']}, 查询: {info['query'][:30]}..."
            
            selected_index = st.selectbox(
                "选择要修改的数据",
                range(len(st.session_state["filtered_data"])),
                format_func=format_item,
                key="modify_data_selector"
            )
            selected_item = st.session_state["filtered_data"][selected_index]
            item_id = selected_item["Result"].get("id")

            st.subheader("当前数据")
            st.json(selected_item, expanded=True)

            st.subheader("修改数据")
            # 使用数据管理器的通用方法构建修改表单
            changes = {}
            editable_fields = manager.get_item_editable_fields(selected_item)
            
            # 动态生成Input部分的表单字段
            if "Input" in editable_fields and editable_fields["Input"]:
                st.write("### Input部分")
                for field_name, field_info in editable_fields["Input"].items():
                    key = f"input_{field_name}"
                    label = field_info["label"]
                    current_value = field_info["value"]
                    widget_type = field_info["type"]
                    
                    if widget_type == "text_input":
                        new_value = st.text_input(label, str(current_value) if current_value else "", key=key)
                        if new_value != (str(current_value) if current_value else ""):
                            changes[f"Input.{field_name}"] = new_value
                    
                    elif widget_type == "text_area":
                        if isinstance(current_value, (dict, list)):
                            display_value = json.dumps(current_value, ensure_ascii=False, indent=2)
                        else:
                            display_value = str(current_value) if current_value else ""
                        
                        new_value = st.text_area(label, display_value, key=key)
                        
                        # 尝试解析JSON
                        if new_value != display_value:
                            try:
                                if field_name in ["history", "env", "metadata"] and new_value.strip():
                                    parsed_value = json.loads(new_value)
                                    changes[f"Input.{field_name}"] = parsed_value
                                else:
                                    changes[f"Input.{field_name}"] = new_value
                            except json.JSONDecodeError:
                                if new_value.strip():
                                    st.warning(f"{label}格式不正确，请输入有效的JSON格式")
                                else:
                                    changes[f"Input.{field_name}"] = new_value

            # 动态生成Result部分的表单字段
            if "Result" in editable_fields and editable_fields["Result"]:
                st.write("### Result部分")
                for field_name, field_info in editable_fields["Result"].items():
                    key = f"result_{field_name}"
                    label = field_info["label"]
                    current_value = field_info["value"]
                    widget_type = field_info["type"]
                    
                    if widget_type == "text_input":
                        new_value = st.text_input(label, str(current_value) if current_value else "", key=key)
                        if new_value != (str(current_value) if current_value else ""):
                            changes[f"Result.{field_name}"] = new_value
                    
                    elif widget_type == "text_area":
                        if isinstance(current_value, (dict, list)):
                            display_value = json.dumps(current_value, ensure_ascii=False, indent=2)
                        else:
                            display_value = str(current_value) if current_value else ""
                        
                        new_value = st.text_area(label, display_value, key=key)
                        
                        if new_value != display_value:
                            try:
                                if field_name == "action" and new_value.strip():
                                    parsed_value = json.loads(new_value)
                                    changes[f"Result.{field_name}"] = parsed_value
                                else:
                                    changes[f"Result.{field_name}"] = new_value
                            except json.JSONDecodeError:
                                if new_value.strip():
                                    st.warning(f"{label}格式不正确，请输入有效的JSON格式")
                                else:
                                    changes[f"Result.{field_name}"] = new_value
                    
                    elif widget_type == "checkbox":
                        new_value = st.checkbox(label, bool(current_value), key=key)
                        if new_value != bool(current_value):
                            changes[f"Result.{field_name}"] = new_value

            # 应用修改
            if st.button("应用修改", key="apply_data_modification"):
                if changes:
                    success = manager.modify_item(data_type=data_type, item_id=item_id, changes=changes)
                    if success:
                            # 保存修改后的数据
                            manager.save_data()
                            st.success("数据修改成功并已保存")
                            # 刷新数据和过滤结果
                            manager.load_data()
                            # 重新应用过滤以更新filtered_data
                            if filter_type == "标签过滤" and tags_input:
                                tags = [tag.strip() for tag in tags_input.split(",")]
                                filtered_data = manager.filter_by_tags(data_type=data_type, tags=tags)
                            elif filter_type == "正则表达式过滤" and pattern:
                                filtered_data = manager.filter_by_regex(data_type=data_type, pattern=pattern)
                            elif filter_type == "大模型语义过滤" and query:
                                filtered_data = manager.filter_by_llm(data_type=data_type, query=query)
                            else:
                                filtered_data = []
                            st.session_state["filtered_data"] = filtered_data
                            st.rerun()
                    else:
                        st.error("数据修改失败")
                else:
                    st.warning("未做任何修改")
    else:
        st.info("请先进行数据筛选")