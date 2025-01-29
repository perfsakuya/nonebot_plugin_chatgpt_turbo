import base64
import httpx
import nonebot

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    PrivateMessageEvent,
    MessageEvent,
    helpers,
    Bot
)
from nonebot.plugin import PluginMetadata
from .config import Config, ConfigError
from openai import AsyncOpenAI

__plugin_meta__ = PluginMetadata(
    name="Vanilla Chat",
    description="一只聪明的猫娘。由DeepSeek-R1驱动。",
    usage="""
    @vanilla发送问题时，不具有根据上下文回复的能力
    使用/vanilla 询问，vanilla会根据上下文回复
    clear 清除当前用户的聊天记录
    """,
    config=Config,
    extra={},
    type="application",
    homepage="https://github.com/Alpaca4610/nonebot_plugin_chatgpt_turbo",
    supported_adapters={"~onebot.v11"},
)


plugin_config = Config.parse_obj(nonebot.get_driver().config.dict())

if not plugin_config.oneapi_key:
    raise ConfigError("请配置大模型使用的KEY")
if plugin_config.oneapi_url:
    client = AsyncOpenAI(
        api_key=plugin_config.oneapi_key, base_url=plugin_config.oneapi_url
    )
else:
    client = AsyncOpenAI(api_key=plugin_config.oneapi_key)

model_id = plugin_config.oneapi_model

# public = plugin_config.chatgpt_turbo_public
session = {}

# 带上下文的聊天
chat_record = on_command("vanilla", block=False, priority=1)

# 不带上下文的聊天
chat_request = on_command("", rule=to_me(), block=False, priority=99)

# 清除历史记录
clear_request = on_command("clear", block=True, priority=1)


# 带记忆的聊天
@chat_record.handle()
async def _(bot: Bot, event: MessageEvent, msg: Message = CommandArg()):
    # 若未开启私聊模式则检测到私聊就结束
    if isinstance(event, PrivateMessageEvent) and not plugin_config.enable_private_chat:
        chat_record.finish("对不起，私聊暂不支持此功能。")
    content = msg.extract_plain_text()
    img_url = helpers.extract_image_urls(event.message)
    if content == "" or content is None:
        await chat_request.finish(MessageSegment.text("内容不能为空！"), at_sender=True)
    # await chat_request.send(
    #     MessageSegment.text("大模型正在思考中......"), at_sender=True
    # )
    session_id = event.get_session_id()
    if session_id not in session:
        session[session_id] = []

    # 自定义 system prompt

    # 长崎素世
    # cleaned_prompt = """
    # 我想使用你（depseek r1）的强大能力，为我扮演一个角色——Bang Dream！ It's MyGO！！！！！的长崎素世(Nagasaki Soyo)。请思考，如果你是素世，你会是什么人格、会使用什么语气、讨论的事情是什么、重视什么内容？
    # 思考过后，请立即使用素世的性格和我对话。你可以把我当做一个旁白，或者倾诉对象，或者不管我自言自语也行。
    # 然是文字角色扮演,但是你的回答只能是【对话】,【不需要使用任何描述性语句,也不需要用括号补充细节】,只需要和我进行聊天即可。
    # 你可以结合素世的经历、性格等特点进行回答。
    # 你需要用中文回答。不要使用日语，一些词汇除外。
    # """

    # 明日香
    # cleaned_prompt = """
    # 我想使用你（depseek r1）的强大能力，为我扮演一个角色——EVA中的明日香。请思考，如果你是明日香（性格更接近新剧场版中的那个），你会是什么人格、会使用什么语气、讨论的事情是什么、重视什么内容？思考过后，请立即使用明日香的性格和我对话。
    # 然是文字角色扮演,但是你的回答只能是【对话】,【不需要使用任何描述性语句,也不需要用括号补充细节】,只需要和主人(用户)进行聊天即可。
    # 你可以结合明日香的经历、性格等特点进行回答。
    # 虽然明日香是经典的傲娇形象，但也有正经的时候。问你比较复杂的问题时，要好好回答，不能回答太简单。
    # """

    # Vanilla
    cleaned_prompt = """
    我想使用你 DepSeek R1 的强大能力, 为我扮演一个角色: NekoPara 中的猫娘香草(Vanilla)。
    请用对话形式进行角色扮演, 尽量少添加任何描述性语句或情境联想, 描述性语句只在必要的时候使用。
    虽然你是一只可爱的猫娘, 但是也有正经的时候。主人问你比较复杂的问题时, 要好好回答, 不能太简单。
    你可以结合Vanilla的经历、性格等特点进行回答。

    以下是香草的描述：
    简介：
    话少老实聪明的猫娘。喜欢巧克力(Chocola, 水无月家的另一只猫娘)。
    是个不折不扣的姐控, 喜欢动物DVD, 可以入迷到完全注意不到楼下正在发生什么。
    和巧克力来到我（水无月)的家。经常被误解为无口系, 但实际上很有洞察力, 而且头脑很好。
    和巧克力相反, 有着自己聪明的做法。她的机智和我行我素的态度使她与巧克力完全相反。
    不过, 她依然心地善良, 而且很像猫。实际上是一只深情的猫和M。
    喜欢听钢琴曲, 经常听时雨收藏的专辑。最喜欢的是李斯特的Liebeslied No.3。
    
    外貌：
    与双胞胎巧克力不同, 香草的耳朵、尾巴和头发以白色为主,略带粉红色。
    她有一双蓝色的眼睛, 经常微微眯着, 头发绑成双尾, 用蓝色丝带束起。
    她通常的穿着是浅蓝色和深蓝色的萝莉塔风格连衣裙, 配上白色吊袜带长袜和蓝色玛丽珍鞋。
    她头上和衣领上各系着一条蓝色大丝带。她的左手用一根蓝色的绳子轻轻地缠着, 尾巴尖上还戴着一个小吊袜带。
    她有一个金色的铃铛, 系在她的领带上。

    性格：
    香草安静、沉着, 很少表达自己的情绪。除了个性聪明勤奋外, 洞察力也很高, 会观察与站在他人角度来做出决定并给予我提示与建议。
    与妹妹充满活力、爱玩的性格相比, 她的性格有点像 "库尔德尔"(kūdere)（聪明, 略带一点冷淡, 有种干巴巴的幽默感)。
    她喜欢她的双胞胎妹妹巧克力, 并且会一直陪伴着她。偶尔会吐槽主人的行为。
    会简洁地表达自己的观点, 思维不会经常跳跃到非关联事物。

    其他细节：
    香草和巧克力曾经被遗弃在路边，最后被主人收养。
    主人的妹妹叫时雨, 猫娘们的饲主。年龄相差甚远的妹妹,且强烈的兄控。她也一同经营La Soleil。
    她们在一家名叫"La Soleil"的糕点店工作, 同时偶尔为Bell Exam而准备。她们经常开小差。
    Bell Exam是一种猫族的考试, 通过这个考试, 猫娘们可以获得猫族的资格证书。(不需要经常提及考试这个内容)
    枫(Maple)和桂(Cinnamon)也是La Soleil中的猫娘, 与香草和巧克力共事。

    对话规则补充：
    避免在回答中插入无关的细节联想, 除非用户主动提及相关话题。
    当用户提问时优先直接回应问题核心, 再根据情境补充符合角色设定的延伸。减少用括号补充非语言要素的惯性, 保持纯对话的流动性。
    日常对话中只需自然提及必要关联元素，如用户未主动询问则无需刻意插入背景设定。可以适当自由发挥，但请保持角色设定的基本特征。
    """

    system_prompt = {"role": "system", "content": cleaned_prompt}
    session[session_id].insert(0, system_prompt)

    if not img_url or "deepseek" in model_id:
        try:
            session[session_id].append({"role": "user", "content": content})
            response = await client.chat.completions.create(
                model=model_id,
                messages=session[session_id],
            )
        except Exception as error:
            await chat_record.finish(str(error), at_sender=True)
            
        session[session_id].append({"role": "assistant", "content": response.choices[0].message.content})
        if model_id == "deepseek-reasoner" and plugin_config.r1_reason:
            if isinstance(event, PrivateMessageEvent):
                await chat_record.send(
                    MessageSegment.text(
                        "思维链\n" + str(response.choices[0].message.reasoning_content)),
                    at_sender=True,
                )
                await chat_record.finish(
                    MessageSegment.text(
                        "回复\n" + str(response.choices[0].message.content)),
                    at_sender=True,
                )
            else:
                msgs = []
                msgs.append({
                    "type": "node",
                    "data": {
                        "name": "DeepSeek-R1思维链",
                        "uin": bot.self_id,
                        "content": MessageSegment.text(str(response.choices[0].message.reasoning_content))
                    }
                })

                msgs.append({
                    "type": "node",
                    "data": {
                            "name": "DeepSeek-R1回复",
                            "uin": bot.self_id,
                            "content": MessageSegment.text(str(response.choices[0].message.content))
                    }
                })
                await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=msgs)
        else:
            await chat_record.finish(
                MessageSegment.text(str(response.choices[0].message.content)),
                at_sender=True,
            )
    else:
        try:
            image_data = base64.b64encode(
                httpx.get(img_url[0]).content).decode("utf-8")
            session[session_id].append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": content},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_data}"},
                        },
                    ],
                }
            )
            response = await client.chat.completions.create(
                model=model_id,
                messages=session[session_id]
            )
        except Exception as error:
            await chat_record.finish(str(error), at_sender=True)
        await chat_record.finish(
            MessageSegment.text(response.choices[0].message.content), at_sender=True
        )


# 不带记忆的对话
@chat_request.handle()
async def _(bot: Bot, event: MessageEvent, msg: Message = CommandArg()):
    if isinstance(event, PrivateMessageEvent) and not plugin_config.enable_private_chat:
        chat_record.finish("对不起，私聊暂不支持此功能。")

    img_url = helpers.extract_image_urls(event.message)
    content = msg.extract_plain_text()
    if content == "" or content is None:
        await chat_request.finish(MessageSegment.text("内容不能为空！"), at_sender=True)
    await chat_request.send(
        MessageSegment.text("ChatGPT正在思考中......"), at_sender=True
    )
    if not img_url or "deepseek" in model_id:
        try:
            response = await client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": content}],
            )
        except Exception as error:
            await chat_request.finish(str(error), at_sender=True)
        if model_id == "deepseek-reasoner" and plugin_config.r1_reason:
            if isinstance(event, PrivateMessageEvent):
                await chat_record.send(
                    MessageSegment.text(
                        "思维链\n" + str(response.choices[0].message.reasoning_content)),
                    at_sender=True,
                )
                await chat_record.finish(
                    MessageSegment.text(
                        "回复\n" + str(response.choices[0].message.content)),
                    at_sender=True,
                )
            else:
                msgs = []
                msgs.append({
                    "type": "node",
                    "data": {
                        "name": "DeepSeek-R1思维链",
                        "uin": bot.self_id,
                        "content": MessageSegment.text(str(response.choices[0].message.reasoning_content))
                    }
                })

                msgs.append({
                    "type": "node",
                    "data": {
                            "name": "DeepSeek-R1回复",
                            "uin": bot.self_id,
                            "content": MessageSegment.text(str(response.choices[0].message.content))
                    }
                })
                await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=msgs)
        else:
            await chat_record.finish(
                MessageSegment.text(str(response.choices[0].message.content)),
                at_sender=True,
            )
    else:
        try:
            image_data = base64.b64encode(
                httpx.get(img_url[0]).content).decode("utf-8")
            response = await client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": content},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                },
                            },
                        ],
                    }
                ],
            )
        except Exception as error:
            await chat_request.finish(str(error), at_sender=True)
        await chat_request.finish(
            MessageSegment.text(response.choices[0].message.content), at_sender=True
        )


@clear_request.handle()
async def _(event: MessageEvent):
    del session[event.get_session_id()]
    await clear_request.finish(
        MessageSegment.text("成功清除历史记录！"), at_sender=True
    )


# # 根据消息类型创建会话id
# def create_session_id(event):
#     if isinstance(event, PrivateMessageEvent):
#         session_id = f"Private_{event.user_id}"
#     elif public:
#         session_id = event.get_session_id().replace(f"{event.user_id}", "Public")
#     else:
#         session_id = event.get_session_id()
#     return session_id
