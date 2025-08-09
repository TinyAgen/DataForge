import streamlit as st
import json
import os
import re

def generate_self_instruct_prompt(input_schema, result_schema):
    """根据Input和Result Schema生成Self-instruct提示词"""
    
    # 获取Schema中的字段描述
    input_fields = []
    if "properties" in input_schema:
        for field, config in input_schema["properties"].items():
            field_type = config.get("type", "string")
            field_desc = config.get("description", f"{field}字段")
            input_fields.append(f"- {field} ({field_type}): {field_desc}")
    
    result_fields = []
    if "properties" in result_schema:
        for field, config in result_schema["properties"].items():
            field_type = config.get("type", "string")
            field_desc = config.get("description", f"{field}字段")
            result_fields.append(f"- {field} ({field_type}): {field_desc}")
    
    # 生成示例格式
    input_example = {}
    if "properties" in input_schema:
        for field, config in input_schema["properties"].items():
            field_type = config.get("type", "string")
            if field_type == "array":
                input_example[field] = []
            elif field_type == "integer":
                input_example[field] = 1
            elif field_type == "boolean":
                input_example[field] = True
            else:
                input_example[field] = f"示例{field}"
    
    result_example = {}
    if "properties" in result_schema:
        for field, config in result_schema["properties"].items():
            field_type = config.get("type", "string")
            if field_type == "array":
                result_example[field] = []
            elif field_type == "integer":
                result_example[field] = 1
            elif field_type == "boolean":
                result_example[field] = True
            else:
                result_example[field] = f"示例{field}"
    
    # 构建Self-instruct提示词
    prompt = f"""# 数据生成任务

你是一个专业的数据生成助手，需要根据以下规格生成高质量的训练数据。

## 任务描述
生成符合指定格式的输入输出对，用于训练大模型。每个数据条目包含Input和Result两部分。

## Input格式规范
Input部分应包含以下字段：
{chr(10).join(input_fields) if input_fields else "- 请根据具体需求定义"}

## Result格式规范  
Result部分应包含以下字段：
{chr(10).join(result_fields) if result_fields else "- 请根据具体需求定义"}

## 数据生成要求
1. **多样性**：生成的数据应覆盖不同场景和用例
2. **真实性**：数据应符合实际使用场景，避免过于简单或重复
3. **一致性**：Input和Result之间应有明确的逻辑关系
4. **完整性**：确保所有必需字段都有合理的值

## 输出格式
请生成一个完整的数据条目，包含Input和Result两部分，格式如下：

```json
[{{
  "Input": {json.dumps(input_example, ensure_ascii=False, indent=4)},
  "Result": {json.dumps(result_example, ensure_ascii=False, indent=4)}
}}]
```

## 生成指南
- 根据Input的内容，生成相应的Result
- 确保数据的逻辑一致性和实用价值
- 可以参考真实场景，但避免使用敏感信息
- 注意字段类型和格式要求

请生成一个符合上述要求的5条数据条目。"""

    return prompt

def extract_data_pairs_from_text(text):
    """从生成的文本中提取Input和Result对"""
    from data_manager import extract_json_from_llm_response
    
    data_pairs = []
    
    # 添加调试信息
    print(f"[DEBUG] 开始解析文本，长度: {len(text)}")
    print(f"[DEBUG] 文本前200字符: {text[:200]}")
    
    try:
        # 使用通用JSON提取函数
        parsed_data = extract_json_from_llm_response(text)
        print(f"[DEBUG] 通用JSON提取结果类型: {type(parsed_data)}")
        
        # 方法1: 如果直接是包含Input和Result的对象
        if isinstance(parsed_data, dict) and "Input" in parsed_data and "Result" in parsed_data:
            data_pairs.append({
                "Input": parsed_data["Input"],
                "Result": parsed_data["Result"]
            })
            print(f"[DEBUG] 方法1成功，提取1个数据对")
            return data_pairs
        
        # 方法2: 如果是对象数组
        if isinstance(parsed_data, list):
            print(f"[DEBUG] 检测到数组，长度: {len(parsed_data)}")
            for i, item in enumerate(parsed_data):
                print(f"[DEBUG] 检查数组项 {i}: {type(item)}, keys: {list(item.keys()) if isinstance(item, dict) else 'N/A'}")
                if isinstance(item, dict) and "Input" in item and "Result" in item:
                    data_pairs.append({
                        "Input": item["Input"],
                        "Result": item["Result"]
                    })
                    print(f"[DEBUG] 数组项 {i} 成功提取")
            if data_pairs:
                print(f"[DEBUG] 方法2成功，提取{len(data_pairs)}个数据对")
                return data_pairs
    except Exception as e:
        print(f"[DEBUG] 通用JSON提取失败: {str(e)}")
        pass
    
    # 备用方法1: 先尝试提取JSON数组
    print(f"[DEBUG] 尝试备用方法1: 直接提取JSON数组")
    try:
        # 尝试找到JSON数组模式
        array_patterns = [
            r'\[(?:[^\[\]]|\{[^{}]*\})*\]',  # 简单数组
            r'\[(?:[^\[\]]|\{(?:[^{}]|\{[^{}]*\})*\})*\]',  # 嵌套数组
        ]
        
        for pattern in array_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    array_data = json.loads(match)
                    if isinstance(array_data, list):
                        print(f"[DEBUG] 找到数组，长度: {len(array_data)}")
                        for i, item in enumerate(array_data):
                            if isinstance(item, dict) and "Input" in item and "Result" in item:
                                data_pairs.append({
                                    "Input": item["Input"],
                                    "Result": item["Result"]
                                })
                                print(f"[DEBUG] 从数组提取数据对 {i}")
                        if data_pairs:
                            print(f"[DEBUG] 备用方法1成功，提取{len(data_pairs)}个数据对")
                            return data_pairs
                except Exception as e:
                    print(f"[DEBUG] 数组解析失败: {str(e)}")
                    continue
    except Exception as e:
        print(f"[DEBUG] 备用方法1异常: {str(e)}")
    
    # 备用方法2: 使用正则表达式逐个提取JSON对象
    print(f"[DEBUG] 尝试备用方法2: 逐个提取JSON对象")
    try:
        # 改进的正则表达式，支持多层嵌套
        object_patterns = [
            # 匹配包含Input和Result的完整对象
            r'\{[^{}]*"Input"[^{}]*"Result"[^{}]*\}',
            r'\{(?:[^{}]|\{[^{}]*\})*"Input"(?:[^{}]|\{[^{}]*\})*"Result"(?:[^{}]|\{[^{}]*\})*\}',
            r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*"Input"(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*"Result"(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}',
        ]
        
        for pattern in object_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            print(f"[DEBUG] 使用模式找到 {len(matches)} 个匹配")
            
            for i, match in enumerate(matches):
                try:
                    parsed = json.loads(match)
                    if isinstance(parsed, dict) and "Input" in parsed and "Result" in parsed:
                        data_pairs.append({
                            "Input": parsed["Input"],
                            "Result": parsed["Result"]
                        })
                        print(f"[DEBUG] 成功解析对象 {i}")
                except Exception as e:
                    print(f"[DEBUG] 对象 {i} 解析失败: {str(e)}")
                    continue
            
            if data_pairs:
                print(f"[DEBUG] 备用方法2成功，提取{len(data_pairs)}个数据对")
                return data_pairs
    except Exception as e:
        print(f"[DEBUG] 备用方法2异常: {str(e)}")
    
    # 备用方法3: 分别提取Input和Result块并配对
    print(f"[DEBUG] 尝试备用方法3: 分别提取Input和Result块")
    if not data_pairs:
        try:
            input_blocks = []
            result_blocks = []
            
            # 提取Input块
            input_patterns = [
                r'"Input"\s*:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
                r'"Input"\s*:\s*(\{(?:[^{}]|\{[^{}]*\})*\})',
            ]
            
            for pattern in input_patterns:
                input_matches = re.findall(pattern, text, re.DOTALL)
                print(f"[DEBUG] Input模式找到 {len(input_matches)} 个匹配")
                for i, match in enumerate(input_matches):
                    try:
                        input_data = json.loads(match)
                        input_blocks.append(input_data)
                        print(f"[DEBUG] 成功解析Input块 {i}")
                    except Exception as e:
                        print(f"[DEBUG] Input块 {i} 解析失败: {str(e)}")
                        continue
                if input_blocks:
                    break
            
            # 提取Result块
            result_patterns = [
                r'"Result"\s*:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
                r'"Result"\s*:\s*(\{(?:[^{}]|\{[^{}]*\})*\})',
            ]
            
            for pattern in result_patterns:
                result_matches = re.findall(pattern, text, re.DOTALL)
                print(f"[DEBUG] Result模式找到 {len(result_matches)} 个匹配")
                for i, match in enumerate(result_matches):
                    try:
                        result_data = json.loads(match)
                        result_blocks.append(result_data)
                        print(f"[DEBUG] 成功解析Result块 {i}")
                    except Exception as e:
                        print(f"[DEBUG] Result块 {i} 解析失败: {str(e)}")
                        continue
                if result_blocks:
                    break
            
            # 配对Input和Result
            min_len = min(len(input_blocks), len(result_blocks))
            print(f"[DEBUG] 准备配对: Input块{len(input_blocks)}个, Result块{len(result_blocks)}个, 可配对{min_len}个")
            
            for i in range(min_len):
                data_pairs.append({
                    "Input": input_blocks[i],
                    "Result": result_blocks[i]
                })
                print(f"[DEBUG] 成功配对数据对 {i}")
                
            if data_pairs:
                print(f"[DEBUG] 备用方法3成功，提取{len(data_pairs)}个数据对")
        except Exception as e:
            print(f"[DEBUG] 备用方法3异常: {str(e)}")
    
    print(f"[DEBUG] 最终结果: 提取了{len(data_pairs)}个数据对")
    return data_pairs

def render_data_pair_editor(pair_id, input_data, result_data, default_data_type, manager):
    """渲染单个数据对的编辑器"""
    st.markdown(f"### 数据对 {pair_id + 1}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Input 数据**")
        edited_input = st.text_area(
            f"Input {pair_id + 1}",
            value=json.dumps(input_data, ensure_ascii=False, indent=2),
            height=200,
            key=f"input_edit_{pair_id}"
        )
    
    with col2:
        st.write("**Result 数据**")
        edited_result = st.text_area(
            f"Result {pair_id + 1}",
            value=json.dumps(result_data, ensure_ascii=False, indent=2),
            height=200,
            key=f"result_edit_{pair_id}"
        )
    
    # 数据集选择
    col_dataset, col_buttons = st.columns([1, 2])
    with col_dataset:
        train_count = len(manager.train_data) if manager.train_data else 0
        val_count = len(manager.val_data) if manager.val_data else 0
        
        individual_data_type = st.radio(
            f"保存到",
            options=["train", "val"],
            format_func=lambda x: f"🎯 训练集({train_count})" if x == "train" else f"✅ 验证集({val_count})",
            horizontal=True,
            key=f"individual_data_type_{pair_id}",
            index=0 if default_data_type == "train" else 1
        )
    
    # 操作按钮
    with col_buttons:
        col_save, col_discard, col_preview = st.columns([1, 1, 1])
        
        with col_save:
            save_clicked = st.button(f"💾 保存", key=f"save_{pair_id}", use_container_width=True, type="primary")
        
        with col_discard:
            discard_clicked = st.button(f"🗑️ 放弃", key=f"discard_{pair_id}", use_container_width=True)
        
        with col_preview:
            if st.button(f"👀 预览", key=f"preview_{pair_id}", use_container_width=True):
                try:
                    input_json = json.loads(edited_input)
                    result_json = json.loads(edited_result)
                    with st.expander(f"数据对 {pair_id + 1} JSON预览", expanded=True):
                        st.json({"Input": input_json, "Result": result_json})
                except Exception as e:
                    st.error(f"JSON格式错误: {str(e)}")
    
    return save_clicked, discard_clicked, edited_input, edited_result, individual_data_type

# 数据生成页面
def data_generation_page(manager):
    st.title("数据生成")
    st.write("使用大模型生成新的数据条目，人工review后保存进数据集")

    # 模型选择
    model = st.selectbox(
        "选择模型",
        ["qwen-max", "qwen-plus", "qwen-turbo"],
        index=0
    )

    # System Prompt管理
    st.subheader("System Prompt管理")
    available_prompts = manager.list_system_prompts()
    prompt_options = ["新建"] + available_prompts
    selected_prompt = st.selectbox("选择或新建System Prompt", prompt_options)

    system_prompt = ""
    if selected_prompt == "新建":
        prompt_name = st.text_input("输入Prompt名称")
        
        # 智能生成System Prompt按钮
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🤖 智能生成提示词", help="根据项目Schema自动生成Self-instruct提示词"):
                if manager.current_project and manager.input_schema and manager.result_schema:
                    generated_prompt = generate_self_instruct_prompt(manager.input_schema, manager.result_schema)
                    st.session_state["generated_prompt"] = generated_prompt
                    st.rerun()
                else:
                    st.warning("⚠️ 请先选择项目并确保项目有完整的Schema配置")
        
        with col2:
            if st.button("👀 预览Schema信息", help="查看当前项目的Schema信息"):
                if manager.current_project and manager.input_schema and manager.result_schema:
                    with st.expander("📋 当前项目Schema信息", expanded=True):
                        col_input, col_result = st.columns(2)
                        with col_input:
                            st.write("**Input Schema:**")
                            st.json(manager.input_schema, expanded=False)
                        with col_result:
                            st.write("**Result Schema:**")
                            st.json(manager.result_schema, expanded=False)
                else:
                    st.warning("⚠️ 当前项目Schema信息不完整")
        
        # 显示生成的提示词或让用户手动输入
        if "generated_prompt" in st.session_state:
            system_prompt = st.text_area(
                "生成的System Prompt内容（可编辑）", 
                value=st.session_state["generated_prompt"], 
                height=500,
                help="这是根据您项目的Schema自动生成的提示词，您可以根据需要进行修改"
            )
            if st.button("🗑️ 清除生成内容"):
                del st.session_state["generated_prompt"]
                st.rerun()
        else:
            system_prompt = st.text_area("输入System Prompt内容", height=500)
        
        if st.button("保存System Prompt"):
            if prompt_name and system_prompt:
                if manager.save_system_prompt(prompt_name, system_prompt):
                    st.success(f"成功保存System Prompt: {prompt_name}")
                    if "generated_prompt" in st.session_state:
                        del st.session_state["generated_prompt"]
                    st.rerun()
                else:
                    st.error("保存System Prompt失败")
            else:
                st.error("Prompt名称和内容不能为空")
    else:
        system_prompt = manager.load_system_prompt(selected_prompt)
        st.text_area("System Prompt内容", system_prompt, height=500)


    # 生成按钮
    if st.button("生成结果"):
        if system_prompt:
            with st.spinner("正在生成数据..."):
                try:
                    # 直接调用LLM，获取原始响应
                    from llm import call_llm
                    prompt = f"{system_prompt}\n\n请自主生成一个用户输入和对应的输出结果，并生成符合现有数据格式的结果，包括id、turn、query_independent、target、processed_query和search。"
                    
                    # 调用LLM获取原始输出
                    raw_output = call_llm(prompt, manager.api_key, model=model).strip()
                    
                    # 存储原始输出
                    st.session_state["raw_llm_output"] = raw_output
                    
                    # 显示原始输出
                    st.success(f"✅ 使用 {model} 模型生成完成！")
                    
                    # 显示原始输出
                    with st.expander("📄 模型原始输出", expanded=True):
                        st.text_area("原始输出内容", raw_output, height=300, key="raw_output_display")
                        
                        # 输出统计信息
                        col_stats1, col_stats2, col_stats3 = st.columns(3)
                        with col_stats1:
                            st.metric("输出长度", f"{len(raw_output)} 字符")
                        with col_stats2:
                            brace_count = raw_output.count("{") + raw_output.count("}")
                            st.metric("JSON括号", f"{brace_count} 个")
                        with col_stats3:
                            lines_count = len(raw_output.split('\n'))
                            st.metric("行数", f"{lines_count} 行")
                    
                    # 尝试解析数据对
                    st.markdown("---")
                    st.write("### 🔍 自动解析结果")
                    
                    # 添加调试开关
                    show_debug = st.checkbox("🐛 显示调试信息", value=False)
                    
                    with st.spinner("正在解析数据对..."):
                        # 重定向print输出以捕获调试信息
                        import io
                        import contextlib
                        
                        debug_output = io.StringIO()
                        with contextlib.redirect_stdout(debug_output):
                            data_pairs = extract_data_pairs_from_text(raw_output)
                        
                        # 显示调试信息
                        if show_debug:
                            debug_text = debug_output.getvalue()
                            if debug_text:
                                with st.expander("🐛 调试信息"):
                                    st.text(debug_text)
                    
                    if data_pairs:
                        st.session_state["extracted_pairs"] = data_pairs
                        st.session_state["pairs_to_process"] = list(range(len(data_pairs)))
                        st.success(f"🎉 成功解析出 {len(data_pairs)} 个数据对！")
                        
                        # 显示解析出的数据对预览
                        with st.expander("👀 解析结果预览"):
                            for i, pair in enumerate(data_pairs):
                                st.write(f"**数据对 {i + 1}:**")
                                col_preview1, col_preview2 = st.columns(2)
                                with col_preview1:
                                    st.write("*Input:*")
                                    st.json(pair["Input"], expanded=False)
                                with col_preview2:
                                    st.write("*Result:*")
                                    st.json(pair["Result"], expanded=False)
                                if i < len(data_pairs) - 1:
                                    st.markdown("---")
                    else:
                        st.warning("⚠️ 无法自动解析出数据对")
                        st.info("💡 可能的原因：")
                        st.markdown("""
                        - 模型没有按预期格式生成JSON
                        - JSON格式不完整或有语法错误
                        - 缺少"Input"和"Result"字段
                        """)
                        
                        # 提供手动解析选项
                        if st.button("🔧 尝试手动修复并重新解析"):
                            st.info("请在上方的原始输出中修改内容，然后点击下方的'重新解析'按钮")
                        
                except Exception as e:
                    st.error(f"生成数据时出错: {str(e)}")
                    st.error(f"错误详情: {type(e).__name__}: {str(e)}")
        else:
            st.error("System Prompt不能为空")
    
    # 重新解析按钮（当有原始输出时显示）
    if "raw_llm_output" in st.session_state:
        if st.button("🔄 重新解析数据对"):
            with st.spinner("正在重新解析..."):
                try:
                    # 获取用户可能修改过的内容
                    modified_output = st.session_state.get("raw_output_display", st.session_state["raw_llm_output"])
                    
                    data_pairs = extract_data_pairs_from_text(modified_output)
                    
                    if data_pairs:
                        st.session_state["extracted_pairs"] = data_pairs
                        st.session_state["pairs_to_process"] = list(range(len(data_pairs)))
                        st.success(f"🎉 重新解析成功！解析出 {len(data_pairs)} 个数据对")
                        st.rerun()
                    else:
                        st.error("❌ 重新解析仍然失败，请检查JSON格式")
                except Exception as e:
                    st.error(f"重新解析时出错: {str(e)}")
    
    # 显示解析出的数据对编辑器
    if "extracted_pairs" in st.session_state and "pairs_to_process" in st.session_state:
        data_pairs = st.session_state["extracted_pairs"]
        pairs_to_process = st.session_state["pairs_to_process"]
        
        if pairs_to_process:
            st.markdown("---")
            st.subheader(f"📝 数据编辑 (剩余 {len(pairs_to_process)} 对)")
            
            # 显示当前数据集状态
            col_dataset1, col_dataset2 = st.columns(2)
            with col_dataset1:
                train_count = len(manager.train_data) if manager.train_data else 0
                st.metric("训练数据集", f"{train_count} 条")
            with col_dataset2:
                val_count = len(manager.val_data) if manager.val_data else 0
                st.metric("验证数据集", f"{val_count} 条")
            
            st.info("💡 每个数据对可以单独选择保存到训练集或验证集")
            
            # 默认数据集类型，用于每个数据对的初始选择
            data_type = "train"
            
            # 为每个数据对渲染编辑器
            pairs_to_remove = []
            
            for i, pair_idx in enumerate(pairs_to_process):
                pair = data_pairs[pair_idx]
                
                with st.container():
                    save_clicked, discard_clicked, edited_input, edited_result, individual_data_type = render_data_pair_editor(
                        pair_idx, pair["Input"], pair["Result"], data_type, manager
                    )
                    
                    if save_clicked:
                        # 保存数据（使用个人选择的数据集类型）
                        try:
                            input_json = json.loads(edited_input)
                            result_json = json.loads(edited_result)
                            
                            new_entry = {
                                "Input": input_json,
                                "Result": result_json
                            }
                            
                            # 确保Result中有必要的字段
                            if "id" not in new_entry["Result"]:
                                new_entry["Result"]["id"] = 0
                            
                            manager.add_generated_data([new_entry], data_type=individual_data_type)
                            
                            dataset_name = "训练数据集" if individual_data_type == "train" else "验证数据集"
                            train_count = len(manager.train_data)
                            val_count = len(manager.val_data)
                            st.success(f"✅ 数据对 {pair_idx + 1} 已保存到{dataset_name}")
                            st.info(f"📊 当前数据量：训练集 {train_count} 条，验证集 {val_count} 条")
                            
                            pairs_to_remove.append(pair_idx)
                            
                        except json.JSONDecodeError as e:
                            st.error(f"❌ 数据对 {pair_idx + 1} JSON格式错误: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ 保存数据对 {pair_idx + 1} 时出错: {str(e)}")
                    
                    elif discard_clicked:
                        st.info(f"🗑️ 已放弃数据对 {pair_idx + 1}")
                        pairs_to_remove.append(pair_idx)
                
                # 分隔线
                if i < len(pairs_to_process) - 1:
                    st.markdown("---")
            
            # 移除已处理的数据对
            if pairs_to_remove:
                remaining_pairs = [p for p in pairs_to_process if p not in pairs_to_remove]
                st.session_state["pairs_to_process"] = remaining_pairs
                
                if not remaining_pairs:
                    # 所有数据对都已处理完毕
                    st.success("🎉 所有数据对已处理完毕！")
                    if "extracted_pairs" in st.session_state:
                        del st.session_state["extracted_pairs"]
                    if "pairs_to_process" in st.session_state:
                        del st.session_state["pairs_to_process"]
                    if "generated_text" in st.session_state:
                        del st.session_state["generated_text"]
                
                st.rerun()
            
            # 批量操作按钮
            st.markdown("---")
            col_batch1, col_batch2 = st.columns([1, 1])
            
            with col_batch1:
                if st.button("🗑️ 全部放弃", use_container_width=True):
                    st.info("已放弃所有剩余数据对")
                    # 清除状态
                    if "extracted_pairs" in st.session_state:
                        del st.session_state["extracted_pairs"]
                    if "pairs_to_process" in st.session_state:
                        del st.session_state["pairs_to_process"]
                    if "generated_text" in st.session_state:
                        del st.session_state["generated_text"]
                    st.rerun()
            
            with col_batch2:
                if st.button("📄 查看原始输出", use_container_width=True):
                    if "generated_text" in st.session_state:
                        with st.expander("原始模型输出", expanded=True):
                            st.text_area("原始文本", st.session_state["generated_text"], height=300)

    # 手动输入数据区域
    st.subheader("手动输入数据")
    
    # 提供示例格式提示
    with st.expander("💡 数据格式示例"):
        st.markdown("""
        **Input 格式示例：**
        ```json
        {
          "history": [],
          "query": "用户的查询内容",
          "env": "",
          "search_results": ""
        }
        ```
        
        **Result 格式示例：**
        ```json
        {
          "id": 1,
          "turn": 1,
          "query_independent": true,
          "target": "search",
          "processed_query": "处理后的查询",
          "search": true
        }
        ```
        """)
    
    manual_input = st.text_area("手动输入Input (JSON格式)", placeholder='{"history": [], "query": "用户查询", "env": "", "search_results": ""}', height=150)
    manual_result = st.text_area("手动输入Result (JSON格式)", placeholder='{"id": 1, "turn": 1, "query_independent": true, "target": "search", "processed_query": "处理后的查询", "search": true}', height=150)

    # 数据集选择
    st.write("### 📊 选择保存目标")
    col_manual1, col_manual2 = st.columns(2)
    with col_manual1:
        train_count = len(manager.train_data) if manager.train_data else 0
        st.metric("训练数据集", f"{train_count} 条")
    with col_manual2:
        val_count = len(manager.val_data) if manager.val_data else 0
        st.metric("验证数据集", f"{val_count} 条")
    
    data_type = st.radio(
        "选择保存目标",
        options=["train", "val"],
        format_func=lambda x: "🎯 训练数据集" if x == "train" else "✅ 验证数据集",
        horizontal=True,
        key="manual_data_type"
    )
    if st.button("保存手动输入数据"):
        if manual_input and manual_result:
            # 分别验证Input和Result的JSON格式
            input_json = None
            result_json = None
            validation_errors = []
            
            # 验证Input格式
            try:
                input_json = json.loads(manual_input)
            except json.JSONDecodeError as e:
                error_line = getattr(e, 'lineno', '未知')
                error_col = getattr(e, 'colno', '未知')
                validation_errors.append(f"**Input** 格式错误：\n- 位置：第 {error_line} 行，第 {error_col} 列\n- 错误：{e.msg}")

            # 验证Result格式
            try:
                result_json = json.loads(manual_result)
            except json.JSONDecodeError as e:
                error_line = getattr(e, 'lineno', '未知')
                error_col = getattr(e, 'colno', '未知')
                validation_errors.append(f"**Result** 格式错误：\n- 位置：第 {error_line} 行，第 {error_col} 列\n- 错误：{e.msg}")
            
            # 如果有验证错误，显示详细信息
            if validation_errors:
                st.error("❌ JSON格式验证失败：")
                for error in validation_errors:
                    st.markdown(error)
                return
            
            try:
                # 创建符合系统格式的数据条目
                new_entry = {
                    "Input": input_json,
                    "Result": result_json
                }
                
                # 确保Result中有必要的字段，如果没有则自动生成
                if "id" not in new_entry["Result"]:
                    # ID会在add_generated_data中自动分配
                    new_entry["Result"]["id"] = 0
                
                # 保存数据
                manager.add_generated_data([new_entry], data_type=data_type)
                
                # 显示成功消息
                dataset_name = "训练数据集" if data_type == "train" else "验证数据集"
                current_count = len(manager.train_data if data_type == 'train' else manager.val_data)
                train_total = len(manager.train_data)
                val_total = len(manager.val_data)
                
                st.success(f"🎉 数据保存成功！")
                st.info(f"📊 已添加到 **{dataset_name}**，当前数据量：{current_count} 条")
                st.info(f"🗂️ 项目总数据量：训练集 {train_total} 条，验证集 {val_total} 条")
                
                # 显示保存的数据预览
                with st.expander("📋 查看保存的数据"):
                    st.json(new_entry, expanded=False)
                
                # 提示用户下一步操作
                st.markdown("💡 您可以继续添加更多数据，或前往 **数据概览** 页面查看所有数据")
                
            except Exception as e:
                st.error(f"❌ 保存数据时出错: {str(e)}")
        else:
            st.error("❌ Input和Result不能为空")