import os
import json
import re
import shutil
from llm import call_llm
from typing import List, Dict, Any, Optional

def extract_json_from_llm_response(response_text: str) -> dict:
    """从LLM响应中提取JSON对象的通用函数"""
    result_json = None
    
    # 方法1: 尝试直接解析（如果整个响应就是JSON）
    try:
        result_json = json.loads(response_text.strip())
        return result_json
    except:
        pass
    
    # 方法2: 尝试提取代码块中的JSON
    code_block_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```json\s*(\[.*?\])\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'```\s*(\[.*?\])\s*```',
    ]
    for pattern in code_block_patterns:
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            try:
                result_json = json.loads(match.group(1))
                return result_json
            except:
                continue
    
    # 方法3: 使用改进的正则表达式提取JSON对象
    json_patterns = [
        r'\{(?:[^{}"]|"(?:[^"\\]|\\.)*")*\}',  # 简单模式
        r'\{(?:[^{}"]|"(?:[^"\\]|\\.)*"|\{(?:[^{}"]|"(?:[^"\\]|\\.)*")*\})*\}',  # 支持一层嵌套
        r'\[(?:[^\[\]"]|"(?:[^"\\]|\\.)*"|\{(?:[^{}"]|"(?:[^"\\]|\\.)*")*\})*\]',  # 数组模式
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        for match in matches:
            try:
                candidate = json.loads(match)
                # 验证JSON是否包含有意义的内容
                if isinstance(candidate, dict) and len(candidate) > 0:
                    return candidate
                elif isinstance(candidate, list) and len(candidate) > 0:
                    return candidate
            except:
                continue
    
    # 方法4: 逐行查找JSON对象
    lines = response_text.split('\n')
    json_lines = []
    brace_count = 0
    in_json = False
    
    for line in lines:
        if '{' in line and not in_json:
            in_json = True
            json_lines = [line]
            brace_count = line.count('{') - line.count('}')
        elif in_json:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0:
                try:
                    json_text = '\n'.join(json_lines)
                    result_json = json.loads(json_text)
                    return result_json
                except:
                    in_json = False
                    json_lines = []
                    brace_count = 0
    
    # 如果所有方法都失败，抛出异常
    raise Exception(f"无法从LLM响应中提取有效的JSON。响应内容：{response_text[:500]}...")

class UniversalDataManager:
    def __init__(self, project_name=None, api_key=None):
        self.api_key = api_key
        self.train_data = []
        self.val_data = []
        self.input_schema = {}
        self.result_schema = {}
        self.current_project = project_name
        
        # 项目根目录
        self.projects_root = "data"
        
        if project_name:
            self.set_project(project_name)
        else:
            # 兼容旧版本，使用默认data目录
            self.data_dir = "data"
            self.system_prompts_dir = "system_prompts"
            if not os.path.exists(self.system_prompts_dir):
                os.makedirs(self.system_prompts_dir)
            if os.path.exists(os.path.join(self.data_dir, "train_data.json")):
                self.load_data()

    def set_project(self, project_name):
        """设置当前项目"""
        self.current_project = project_name
        self.data_dir = os.path.join(self.projects_root, project_name)
        self.system_prompts_dir = os.path.join(self.data_dir, "system_prompts")
        
        # 创建项目目录结构
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.system_prompts_dir):
            os.makedirs(self.system_prompts_dir)
            
        # 加载项目配置
        self.load_project_config()
        # 加载数据
        if os.path.exists(os.path.join(self.data_dir, "train_data.json")):
            self.load_data()

    def create_project(self, project_name, input_schema, result_schema):
        """创建新项目"""
        project_dir = os.path.join(self.projects_root, project_name)
        
        if os.path.exists(project_dir):
            raise ValueError(f"项目 {project_name} 已存在")
            
        # 创建项目目录结构
        os.makedirs(project_dir)
        os.makedirs(os.path.join(project_dir, "system_prompts"))
        
        # 保存配置文件
        config = {
            "input_schema": input_schema,
            "result_schema": result_schema,
            "created_at": json.dumps({"timestamp": "auto"})
        }
        
        with open(os.path.join(project_dir, "config.json"), 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        # 初始化空数据文件
        with open(os.path.join(project_dir, "train_data.json"), 'w', encoding='utf-8') as f:
            json.dump([], f)
        with open(os.path.join(project_dir, "val_data.json"), 'w', encoding='utf-8') as f:
            json.dump([], f)
            
        print(f"项目 {project_name} 创建成功")

    def list_projects(self):
        """列出所有项目"""
        if not os.path.exists(self.projects_root):
            return []
        return [d for d in os.listdir(self.projects_root) 
                if os.path.isdir(os.path.join(self.projects_root, d)) and 
                os.path.exists(os.path.join(self.projects_root, d, "config.json"))]

    def delete_project(self, project_name):
        """删除项目"""
        project_dir = os.path.join(self.projects_root, project_name)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            print(f"项目 {project_name} 已删除")
        else:
            raise ValueError(f"项目 {project_name} 不存在")

    def load_project_config(self):
        """加载项目配置"""
        if not self.current_project:
            return
            
        config_path = os.path.join(self.data_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.input_schema = config.get("input_schema", {})
                self.result_schema = config.get("result_schema", {})

    def save_project_config(self, input_schema=None, result_schema=None):
        """保存项目配置"""
        if not self.current_project:
            return False
            
        if input_schema:
            self.input_schema = input_schema
        if result_schema:
            self.result_schema = result_schema
            
        config = {
            "input_schema": self.input_schema,
            "result_schema": self.result_schema
        }
        
        config_path = os.path.join(self.data_dir, "config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True

    def load_data(self):
        """加载训练和验证数据"""
        try:
            with open(os.path.join(self.data_dir, "train_data.json"), 'r', encoding='utf-8') as f:
                self.train_data = json.load(f)
            with open(os.path.join(self.data_dir, "val_data.json"), 'r', encoding='utf-8') as f:
                self.val_data = json.load(f)
            print(f"成功加载数据: 训练集{len(self.train_data)}条, 验证集{len(self.val_data)}条")
        except Exception as e:
            print(f"加载数据时出错: {str(e)}")
            raise

    def save_data(self):
        """保存数据到文件"""
        try:
            with open(os.path.join(self.data_dir, "train_data.json"), 'w', encoding='utf-8') as f:
                json.dump(self.train_data, f, ensure_ascii=False, indent=2)
            with open(os.path.join(self.data_dir, "val_data.json"), 'w', encoding='utf-8') as f:
                json.dump(self.val_data, f, ensure_ascii=False, indent=2)
            print("数据保存成功")
        except Exception as e:
            print(f"保存数据时出错: {str(e)}")
            raise

    def filter_by_tags(self, data_type="train", tags=None):
        """通过标签过滤数据 - 基于项目配置动态适配数据结构"""
        if tags is None or not tags:
            return self.train_data if data_type == "train" else self.val_data

        data = self.train_data if data_type == "train" else self.val_data
        filtered_data = []

        for item in data:
            # 获取主要文本字段进行搜索
            search_texts = []
            
            # 从Input中提取文本字段
            if "Input" in item:
                input_data = item["Input"]
                # 根据配置或常见字段名提取文本
                text_fields = ["current_query", "query", "processed_query", "user_input"]
                for field in text_fields:
                    if field in input_data and isinstance(input_data[field], str):
                        search_texts.append(input_data[field])
                
                # 处理历史对话
                if "history" in input_data and isinstance(input_data["history"], list):
                    for msg in input_data["history"]:
                        if isinstance(msg, dict) and "content" in msg:
                            search_texts.append(msg["content"])
            
            # 从Result中提取文本字段
            if "Result" in item:
                result_data = item["Result"]
                text_fields = ["intent", "response", "processed_query", "target"]
                for field in text_fields:
                    if field in result_data and isinstance(result_data[field], str):
                        search_texts.append(result_data[field])
            
            # 在所有提取的文本中搜索标签
            combined_text = " ".join(search_texts).lower()
            if all(tag.lower() in combined_text for tag in tags):
                filtered_data.append(item)

        print(f"标签过滤结果: {len(filtered_data)}条数据")
        return filtered_data

    def filter_by_regex(self, data_type="train", pattern=""):
        """通过正则表达式过滤数据"""
        if not pattern:
            return self.train_data if data_type == "train" else self.val_data

        data = self.train_data if data_type == "train" else self.val_data
        filtered_data = []
        regex = re.compile(pattern)

        for item in data:
            # 搜索Input和Result中的文本
            item_str = json.dumps(item, ensure_ascii=False)
            if regex.search(item_str):
                filtered_data.append(item)

        print(f"正则过滤结果: {len(filtered_data)}条数据")
        return filtered_data

   

    def modify_item(self, data_type="train", item_id=None, changes=None):
        """修改数据条目"""
        if item_id is None or changes is None:
            print("缺少必要参数")
            return False

        data = self.train_data if data_type == "train" else self.val_data

        for item in data:
            if item["Result"].get("id") == item_id:
                # 应用更改
                for key, value in changes.items():
                    # 支持嵌套路径，如 "Result.processed_query"
                    parts = key.split('.')
                    current = item
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                print(f"成功修改ID为{item_id}的数据条目")
                return True

        print(f"未找到ID为{item_id}的数据条目")
        return False

    def save_system_prompt(self, prompt_name, prompt_content):
        """保存system prompt到文件"""
        prompt_path = os.path.join(self.system_prompts_dir, f"{prompt_name}.txt")
        try:
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            print(f"成功保存system prompt到 {prompt_path}")
            return True
        except Exception as e:
            print(f"保存system prompt时出错: {str(e)}")
            return False

    def load_system_prompt(self, prompt_name):
        """从文件加载system prompt"""
        prompt_path = os.path.join(self.system_prompts_dir, f"{prompt_name}.txt")
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"加载system prompt时出错: {str(e)}")
            return None

    def list_system_prompts(self):
        """列出所有可用的system prompt"""
        if not os.path.exists(self.system_prompts_dir):
            return []
        prompts = []
        for filename in os.listdir(self.system_prompts_dir):
            if filename.endswith(".txt"):
                prompts.append(filename[:-4])  # 移除.txt后缀
        return prompts

    def generate_new_data(self, num_entries=10, model="qwen-max"):
        """通过大模型生成新数据"""
        if not self.api_key:
            raise ValueError("API密钥未设置，请先设置API密钥")
            
        new_entries = []

        for i in range(num_entries):
            # 生成用户查询
            query_prompt = "生成一个关于视频搜索的用户查询，主题可以是综艺、健身、音乐等，内容要具体。"
            try:
                query = call_llm(query_prompt, self.api_key, model=model).strip()
                print(f"生成查询 {i+1}/{num_entries}: {query}")

                # 生成对应的处理结果
                result_prompt = f"用户查询: '{query}'\n\n请生成一个符合现有数据格式的Result字段，包括id、turn、query_independent、target、processed_query和search。"
                result = call_llm(result_prompt, self.api_key, model=model).strip()
                # 使用正则表达式提取JSON内容
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if not json_match:
                    raise Exception("无法从LLM响应中提取JSON")
                result_json = json.loads(json_match.group())

                # 构建新条目
                new_entry = {
                    "Input": {
                        "history": [],
                        "query": query,
                        "env": "",
                        "search_results": ""
                    },
                    "Result": result_json
                }
                new_entries.append(new_entry)
            except Exception as e:
                print(f"生成第{i+1}条数据时出错: {str(e)}")

        print(f"成功生成{len(new_entries)}/{num_entries}条新数据")
        return new_entries

    def add_generated_data(self, new_entries, data_type="train"):
        """将生成的数据添加到数据集中"""
        if data_type == "train":
            # 确保ID唯一
            max_id = max(item["Result"].get("id", 0) for item in self.train_data) if self.train_data else 0
            for entry in new_entries:
                max_id += 1
                entry["Result"]["id"] = max_id
            self.train_data.extend(new_entries)
        else:
            max_id = max(item["Result"].get("id", 0) for item in self.val_data) if self.val_data else 0
            for entry in new_entries:
                max_id += 1
                entry["Result"]["id"] = max_id
            self.val_data.extend(new_entries)

        print(f"成功添加{len(new_entries)}条新数据到{data_type}数据集")
        self.save_data()

    def filter_combined(self, data_type: str = "train", filters: Optional[List[Dict[str, Any]]] = None, data: Optional[List[Dict[str, Any]]] = None, callback=None) -> List[Dict[str, Any]]:
        """组合多种过滤方式

        Args:
            data_type: 数据集类型，可选值为"train"或"val"
            filters: 过滤配置列表，每个配置包含过滤类型和参数
                     例如: [
                         {"type": "tags", "params": {"tags": ["综艺", "音乐"]}},
                         {"type": "llm", "params": {"query": "搞笑视频", "model": "qwen-max"}}
                     ]
            data: 可选的输入数据列表，如果不提供则使用默认数据集
            callback: 进度回调函数，接收消息和进度值(0-1)
                      
        Returns:
            过滤后的数据列表
        """
        if filters is None or not filters:
            return self.train_data if data_type == "train" else self.val_data

        # 初始数据
        filtered_data = data if data is not None else (self.train_data if data_type == "train" else self.val_data)
        total_steps = len(filters)

        for step_idx, filter_config in enumerate(filters):
            filter_type = filter_config.get("type")
            params = filter_config.get("params", {})

            # 更新进度
            if callback:
                step_progress = (step_idx + 1) / total_steps
                callback(f"正在执行第{step_idx + 1}/{total_steps}步过滤: {filter_type}", progress=step_progress)

            if filter_type == "tags":
                filtered_data = self.filter_by_tags(data_type=data_type, tags=params.get("tags"), data=filtered_data)
            elif filter_type == "regex":
                filtered_data = self.filter_by_regex(data_type=data_type, pattern=params.get("pattern"), data=filtered_data)
            elif filter_type == "llm":
                # 获取模型参数，如果没有则使用默认值
                model = params.get("model", "qwen-plus")
                # 为LLM过滤创建子回调函数，显示更详细的进度
                def llm_sub_callback(message, progress):
                    if callback:
                        overall_progress = step_idx / total_steps + progress / total_steps
                        callback(f"第{step_idx + 1}/{total_steps}步 (LLM): {message}", progress=overall_progress)
                filtered_data = self.filter_by_llm(data_type=data_type, query=params.get("query"), data=filtered_data, callback=llm_sub_callback, model=model)
            else:
                print(f"未知的过滤类型: {filter_type}")

        print(f"组合过滤结果: {len(filtered_data)}条数据")
        return filtered_data

    # 修改现有过滤方法以支持传入数据参数
    def filter_by_tags(self, data_type: str = "train", tags: Optional[List[str]] = None, data: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """通过标签过滤数据 - 基于项目配置动态适配数据结构"""
        if tags is None or not tags:
            return self.train_data if data_type == "train" else self.val_data

        # 使用传入的数据或默认数据
        data = data if data is not None else (self.train_data if data_type == "train" else self.val_data)
        filtered_data = []

        for item in data:
            # 获取主要文本字段进行搜索
            search_texts = []
            
            # 从Input中提取文本字段
            if "Input" in item:
                input_data = item["Input"]
                # 根据配置或常见字段名提取文本
                text_fields = ["current_query", "query", "processed_query", "user_input"]
                for field in text_fields:
                    if field in input_data and isinstance(input_data[field], str):
                        search_texts.append(input_data[field])
                
                # 处理历史对话
                if "history" in input_data and isinstance(input_data["history"], list):
                    for msg in input_data["history"]:
                        if isinstance(msg, dict) and "content" in msg:
                            search_texts.append(msg["content"])
            
            # 从Result中提取文本字段
            if "Result" in item:
                result_data = item["Result"]
                text_fields = ["intent", "response", "processed_query", "target"]
                for field in text_fields:
                    if field in result_data and isinstance(result_data[field], str):
                        search_texts.append(result_data[field])
            
            # 在所有提取的文本中搜索标签
            combined_text = " ".join(search_texts).lower()
            if all(tag.lower() in combined_text for tag in tags):
                filtered_data.append(item)

        print(f"标签过滤结果: {len(filtered_data)}条数据")
        return filtered_data

    def filter_by_regex(self, data_type: str = "train", pattern: str = "", data: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """通过正则表达式过滤数据"""
        if not pattern:
            return self.train_data if data_type == "train" else self.val_data

        # 使用传入的数据或默认数据
        data = data if data is not None else (self.train_data if data_type == "train" else self.val_data)
        filtered_data = []
        regex = re.compile(pattern)

        for item in data:
            # 搜索Input和Result中的文本
            item_str = json.dumps(item, ensure_ascii=False)
            if regex.search(item_str):
                filtered_data.append(item)

        print(f"正则过滤结果: {len(filtered_data)}条数据")
        return filtered_data

    def filter_by_llm(self, data_type: str = "train", query: str = "", data: Optional[List[Dict[str, Any]]] = None, callback=None, model="qwen-max") -> List[Dict[str, Any]]:
        """通过大模型语义过滤数据"""
        if not query:
            return self.train_data if data_type == "train" else self.val_data

        if not self.api_key:
            raise ValueError("API密钥未设置，请先设置API密钥")

        # 使用传入的数据或默认数据
        data = data if data is not None else (self.train_data if data_type == "train" else self.val_data)
        total_items = len(data)
        filtered_data = []
        processed_count = 0

        # 为每条数据单独调用LLM进行判断
        for item in data:
            processed_count += 1
            item_id = item["Result"].get("id", processed_count)
            input_query=json.dumps(item, ensure_ascii=False, indent=2)        # 构建单条数据的提示
            prompt = f"用户查询: '{query}'\n\n数据条目查询: '{input_query}'\n\n请判断该数据条目是否与用户查询语义相关。仅返回'true'或'false'，不要包含其他文本。"
            print(f"正在处理第{processed_count}/{total_items}条数据 (ID: {item_id}), 模型: {model}")
            # 调用回调函数报告进度
            # if callback:
            #     callback(f"正在处理第{processed_count}/{total_items}条数据 (ID: {item_id})", progress=processed_count/total_items)

            try:
                # 调用LLM
                response = call_llm(prompt, self.api_key, model=model)
                # 解析响应
                is_relevant = response.strip().lower() == 'true'
                if is_relevant:
                    filtered_data.append(item)
            except Exception as e:
                print(f"处理ID为{item_id}的数据时出错: {str(e)}")
                # 出错时跳过该数据
                continue

        # if callback:
        #     callback(f"过滤完成，共找到{len(filtered_data)}条相关数据", progress=1.0)
        print(f"LLM过滤结果: {len(filtered_data)}条数据")
        return filtered_data

    def get_item_display_info(self, item):
        """提取数据项的显示信息 - 根据项目配置动态适配"""
        display_info = {
            "id": "N/A",
            "query": "N/A", 
            "main_text": "N/A"
        }
        
        # 提取ID
        if "Result" in item:
            display_info["id"] = item["Result"].get("id", "N/A")
        
        # 提取主要查询文本 - 按优先级尝试不同字段
        if "Input" in item:
            input_data = item["Input"]
            query_fields = ["current_query", "query", "user_input", "processed_query"]
            for field in query_fields:
                if field in input_data and input_data[field]:
                    display_info["query"] = str(input_data[field])
                    break
        
        # 提取主要文本内容用于显示
        texts = []
        if display_info["query"] != "N/A":
            texts.append(display_info["query"])
        
        if "Result" in item:
            result_data = item["Result"]
            # 添加意图和响应等关键信息
            if "intent" in result_data:
                texts.append(f"意图:{result_data['intent']}")
            if "response" in result_data:
                texts.append(f"回复:{result_data['response'][:50]}...")
        
        display_info["main_text"] = " | ".join(texts) if texts else "N/A"
        
        return display_info

    def get_item_editable_fields(self, item):
        """获取数据项的可编辑字段 - 根据项目配置动态适配"""
        editable_fields = {}
        
        # 从Input中提取可编辑字段
        if "Input" in item:
            input_data = item["Input"]
            editable_fields["Input"] = {}
            
            # 根据schema或常见字段定义可编辑字段
            input_field_types = {
                "current_query": "text_input",
                "query": "text_input", 
                "user_input": "text_input",
                "processed_query": "text_input",
                "history": "text_area",
                "env": "text_area",
                "metadata": "text_area",
                "search_results": "text_area"
            }
            
            for field, widget_type in input_field_types.items():
                if field in input_data:
                    editable_fields["Input"][field] = {
                        "value": input_data[field],
                        "type": widget_type,
                        "label": field.replace("_", " ").title()
                    }
        
        # 从Result中提取可编辑字段
        if "Result" in item:
            result_data = item["Result"]
            editable_fields["Result"] = {}
            
            result_field_types = {
                "id": "text_input",
                "intent": "text_input",
                "response": "text_area",
                "processed_query": "text_input",
                "target": "text_input",
                "search": "checkbox",
                "action": "text_area"
            }
            
            for field, widget_type in result_field_types.items():
                if field in result_data:
                    editable_fields["Result"][field] = {
                        "value": result_data[field],
                        "type": widget_type,
                        "label": field.replace("_", " ").title()
                    }
        
        return editable_fields

    def generate_forward_data(self, system_prompt, user_input, model="qwen-max"):
        """Forward模式: 基于系统提示+用户输入生成结果"""
        if not self.api_key:
            raise ValueError("API密钥未设置，请先设置API密钥")

        # 构建提示
        prompt = f"{system_prompt}\n\n用户输入: {user_input}\n\n请生成符合现有数据格式的结果，包括id、turn、query_independent、target、processed_query和search。"

        try:
            # 调用LLM
            result = call_llm(prompt, self.api_key, model=model).strip()
            # 使用正则表达式提取JSON内容
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if not json_match:
                raise Exception("无法从LLM响应中提取JSON")
            result_json = json.loads(json_match.group())

            # 构建新条目
            new_entry = {
                "Input": {
                    "history": [],
                    "query": user_input,
                    "env": "",
                    "search_results": ""
                },
                "Result": result_json
            }
            return new_entry
        except Exception as e:
            print(f"生成Forward模式数据时出错: {str(e)}")
            raise

    def generate_backward_data(self, system_prompt, expected_output, model="qwen-max"):
        """Backward模式: 基于系统提示+期望输出反推用户输入"""
        if not self.api_key:
            raise ValueError("API密钥未设置，请先设置API密钥")

        # 构建提示
        prompt = f"{system_prompt}\n\n期望输出: {expected_output}\n\n请反推生成可能的用户输入，并生成符合现有数据格式的结果，包括id、turn、query_independent、target、processed_query和search。"

        try:
            # 调用LLM
            result = call_llm(prompt, self.api_key, model=model).strip()
            # 使用正则表达式提取JSON内容
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if not json_match:
                raise Exception("无法从LLM响应中提取JSON")
            result_json = json.loads(json_match.group())

            # 从结果中提取用户输入
            user_input = result_json.get("user_input", "")

            # 构建新条目
            new_entry = {
                "Input": {
                    "history": [],
                    "query": user_input,
                    "env": "",
                    "search_results": ""
                },
                "Result": result_json
            }
            return new_entry
        except Exception as e:
            print(f"生成Backward模式数据时出错: {str(e)}")
            raise

    def generate_self_instruct_data(self, system_prompt, model="qwen-max"):
        """Self-instruct模式: 由模型自主生成符合格式的输入输出对"""
        if not self.api_key:
            raise ValueError("API密钥未设置，请先设置API密钥")

        # 构建提示
        prompt = f"{system_prompt}\n\n请自主生成一个用户输入和对应的输出结果，并生成符合现有数据格式的结果，包括id、turn、query_independent、target、processed_query和search。"

        try:
            # 调用LLM
            result = call_llm(prompt, self.api_key, model=model).strip()
            
            # 使用改进的JSON提取函数
            result_json = extract_json_from_llm_response(result)
            
            # 如果直接返回了完整的数据结构，直接使用
            if "Input" in result_json and "Result" in result_json:
                return result_json
            
            # 如果返回的是数组，取第一个元素
            if isinstance(result_json, list) and len(result_json) > 0:
                first_item = result_json[0]
                if "Input" in first_item and "Result" in first_item:
                    return first_item
            
            # 从结果中提取用户输入
            user_input = result_json.get("user_input", result_json.get("query", ""))

            # 构建新条目
            new_entry = {
                "Input": {
                    "history": [],
                    "query": user_input,
                    "env": "",
                    "search_results": ""
                },
                "Result": result_json
            }
            return new_entry
        except Exception as e:
            print(f"生成Self-instruct模式数据时出错: {str(e)}")
            raise

# 为了向后兼容，保留VideoDataManager别名
VideoDataManager = UniversalDataManager

def main():
    # 创建数据管理器实例
    from dotenv import load_dotenv
    load_dotenv(override=True)
    manager = UniversalDataManager(api_key=os.getenv("DASHSCOPE_API_KEY"))
    # 示例用法
    print("\n=== 标签过滤示例 ===")
    filtered_by_tags = manager.filter_by_tags(tags=["综艺"])
    print(f"找到{len(filtered_by_tags)}条数据")

    print("\n=== 正则过滤示例 ===")
    filtered_by_regex = manager.filter_by_regex(pattern=r"2025")
    print(f"找到{len(filtered_by_regex)}条数据")

    print("\n=== 大模型过滤示例 ===")
    filtered_by_llm = manager.filter_by_llm(query="是否与音乐相关")
    print(f"找到{len(filtered_by_llm)}条数据")
    if filtered_by_llm:
        print(f"  相关数据ID: {[item['Result'].get('id') for item in filtered_by_llm]}")




    # print("\n=== 生成新数据示例 ===")
    # new_data = manager.generate_new_data(num_entries=2)
    # print("生成的新数据:")
    # for idx, entry in enumerate(new_data):
    #     print(f"{idx+1}. 查询: {entry['Input']['query']}")

    # 询问用户是否添加生成的数据
    # 实际使用时可以添加交互确认

if __name__ == "__main__":
    main()