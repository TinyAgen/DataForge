from dashscope import Generation
import time 

def call_llm(prompt, api_key, model="qwen-max"):
    """调用LLM"""
    try:
        # 记录耗时
        print(f"api key: {api_key}")
        print(prompt)
        print(model)
        start_time = time.time()    
        response = Generation.call(
            api_key=api_key,  # 显式传入API Key
            model=model,
            prompt=prompt,
            max_tokens=2048,
            temperature=0.1,
            timeout=20,
        )
        if response is None:
            raise Exception("API调用返回为空")
        if not hasattr(response, 'output') or not hasattr(response.output, 'text'):
            raise Exception(f"API返回格式异常: {response}")
        end_time = time.time()
        print(f"LLM调用耗时: {end_time - start_time} 秒")
        return response.output.text
    except Exception as e:
        print(f"调用LLM时发生错误: {str(e)}")
        raise



if __name__ == "__main__":
    prompt = """用户查询: '是否音乐相关'

数据条目查询: '{
  "Input": {
    "history": [
      {
        "role": "user",
        "content": "最近有什么热门综艺可以看啊？"
      },
      {
        "role": "agent",
        "content": "您偏好哪种类型的综艺呢？比如音乐类、真人秀还是脱口秀呀？"
      }
    ],
    "query": "我想看音乐类的综艺，最好是歌手竞技那种。",
    "env": "无无",
    "search_results": "无"
  },
  "Result": {
    "id": 1,
    "turn": 2,
    "query_independent": true,
    "target": "search",
    "processed_query": "MUST: video_type: 音乐_1|video_category: 综艺_3|video_summary: 歌手竞技",
    "search": true
  }
}'

请判断该数据条目是否与用户查询语义相关。仅返回'true'或'false'，不要包含其他文本。"""
    from dotenv import load_dotenv
    import os 
    load_dotenv(override=True)
    api_key = os.getenv("DASHSCOPE_API_KEY")
    model = "qwen-turbo"
    response = call_llm(prompt, api_key, model)
    print(response)