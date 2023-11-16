import pandas as pd
import tiktoken
import openai
import pprint
openai.api_base = "https://openkey.cloud/v1"
openai.api_key = "sk-erW8GHP4BsDPkrxbB8972a055470491e859f50A49f846eDe"
input_df = pd.read_csv('D:\\Temp\\2021\\processed\\2011stuff',nrows=100)
#output_df = pd.DataFrame(columns=['公诉机关', '被告人', '原告', '案件起因经过', '被告辩护', '法院裁决结果以及理由', '陈列并且解释引用的法规'])
initial_data = { '标题': [], '案件类型': [], '文书': [],'公诉机关': [], '被告人': [], '原告': [] , '案件起因经过': [], '被告辩护': [], '法院裁决结果以及理由': [], '非常具体陈列并且解释引用的法规': [],'gpt': []}
df = pd.DataFrame(initial_data)
csv_filename = 'D:\\Temp\\2021\\processed\\demo_result.csv'
df.to_csv(csv_filename, mode='a', header=False, index=False, encoding='utf-8')


def count_tokens(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens


role_ass = [ {"role": "system", "content":
			"你是一名非常专业的中国律师，你现在的工作是从法律文书中分类出一些信息,这是一份汇报你无需使用礼貌用语，你必须做到能把所提供的信息以段落的形式陈述出来,你的回复需要尽可能的长，你的回复长度需要尽量达到你所被规定的最大token数量，你的工作是陈述而不是总结所以请不忽略任何细节，你的回复必须足够的长，你的回复必须遵守以下格式：/n “公诉机关”, “被告人” ，“原告”，“案件起因经过”，“被告辩护”，“法院裁决结果以及理由”， “引用的法规”， 以下是全部的法律文书，你的信息提取必须做到非常详细，保证能概括到所有提供的信息，如果有信息未被覆盖，请写“无” "} ]
def extraction(case_title, case_type, instrument):
	message = "以下是文书主体\n标题："+case_title+"\n"+"案件类型："+case_type+"\n文书内容:"+instrument
	token_count = count_tokens(message)
	response_token = int(token_count * 0.5)
	if token_count <=2500:
		model_name = "gpt-3.5-turbo-16k"
		max_token = 4000;
		if token_count <= 500:
			message = "这一份文书也许信息较少，但是请必须按照格式回复" + message
		else:
			message = "你的回复token数量不能低于"+str(response_token)+"token\n" + message
	else:
		model_name = "gpt-3.5-turbo-1"
		if int(token_count * 3 / 2)  < 16000:
			max_token = int(token_count * 3 / 2)
		else: 
			max_token = 15999
		message = "你的回复token数量不能低于"+str(response_token)+"token\n" + message
	
	#print("input:\n"+message)
	
	if message:
		temp_messages = [ {"role": "system", "content":
			"你是一名非常专业的中国律师，你现在的工作是从法律文书中分类出一些信息,这是一份汇报你无需使用礼貌用语，你必须做到能把所提供的信息以段落的形式陈述出来,你的回复需要尽可能的长，你的回复长度需要尽量达到你所被规定的最大token数量，你的工作是陈述而不是总结所以请不忽略任何细节，你的回复必须足够的长，你的回复必须遵守以下格式：/n “公诉机关”, “被告人” ，“原告”，“案件起因经过”，“被告辩护”，“法院裁决结果以及理由”， “引用的法规”， 以下是全部的法律文书，你的信息提取必须做到非常详细，保证能概括到所有提供的信息，如果有信息未被覆盖，请写“无” "} ]

		temp_messages.append(
			{"role": "user", "content": message},
		)
		
		chat = openai.ChatCompletion.create(
			model=model_name, 
			messages=temp_messages,
			max_tokens=token_count,
			temperature=0.9,

		)
		#print("----------------\nmessages into gpt is:\n")
		#pprint.pprint(role_ass)
		temp_messages = []

		reply = chat.choices[0].message.content

		output_token = count_tokens(reply)
		titles = ["公诉机关：","被告人：","原告：","案件起因经过：","被告辩护：","法院裁决结果以及理由：","引用的法规："]
		initial_data = { '标题': [], '案件类型': [], '文书': [],'公诉机关': [], '被告人': [], '原告': [] , '案件起因经过': [], '被告辩护': [], '法院裁决结果以及理由': [], '引用的法规': []}
		sections = {}
		
		for i in range(len(titles)-1):
			start_idx = reply.find(titles[i]) + len(titles[i])
			if start_idx == -1:
				sections[titles[i][:-1]] = "无"
				continue
			end_idx = reply.find(titles[i+1])
			if end_idx == -1:
				if i != 5:
					end_idx = reply.find(titles[i+2])
			content = reply[start_idx:end_idx].strip()
			sections[titles[i][:-1]] = content
			
		start_idx = reply.find(titles[6]) + len(titles[6])
		content = reply[start_idx:].strip()
		sections[titles[6][:-1]] = content
		
		new_data = {
        	'标题': [case_title],
        	'案件类型': [case_type],
        	'文书': [case_information],
    		'公诉机关': [sections["公诉机关"]],
     		'被告人': [sections["被告人"]],
     		'原告': [sections["原告"]],
     		'案件起因经过': [sections["案件起因经过"]],
	 		'被告辩护': [sections["被告辩护"]],
    		'法院裁决结果以及理由': [sections["法院裁决结果以及理由"]],
    		'非常具体陈列并且解释引用的法规': [sections["引用的法规"]],
			'gpt':[reply]
    	}
	
		df_new = pd.DataFrame(new_data)
		df_new.to_csv(csv_filename, mode='a', header=False, index=False, encoding='utf-8')
    	
		# Print for verification
		#print(f"ChatGPT: {reply} \n")
		
		for key, value in sections.items():
			print("++++++")
			print(key, "000", value)
			print("------")
   		
		
		print(f"model name: {model_name},  token_limit: {max_token} , reply token：{output_token}”\n ")
		#messages.append({"role": "assistant", "content": reply})

"""title = input("case title:")
type = input("case type: ")
text = input("text:")
"""

for index, row in input_df.iterrows():
    case_information = row['文书内容']
    if count_tokens(case_information) < 600:
        continue
    case_title = row['标题']
    case_type = row['案件类型']
    
    
    #print(case_information)
    
    extraction(case_title,case_type,case_information)

