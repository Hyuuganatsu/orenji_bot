# python
import os

# ariadne
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, ParamMatch, RegexResult, UnionMatch, SpacePolicy
from graia.ariadne.model import Group, Member
from loguru import logger

# saya
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# project
from config.module_config import module_config_manager

saya = Saya.current()
channel = Channel.current()

# Hardcoded admin groups - modify these IDs as needed
ADMIN_GROUPS = {"303488479"}  # Replace with actual admin group IDs

@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(FullMatch("/groups"))],
    )
)
async def get_all_groups_command(app: Ariadne, group: Group, member: Member):
    """Handle /groups command to list all groups the bot is in (must trigger this command in an admin group)"""
    group_id = str(group.id)
    
    # Check if this is an admin group
    if group_id not in ADMIN_GROUPS:
        await app.send_message(group, MessageChain(Plain("此命令仅限管理群组使用。")))
        return
    
    all_groups = await get_all_groups(app)
    
    if not all_groups:
        await app.send_message(group, MessageChain(Plain("无法获取群组列表或bot未加入任何群组。")))
        return
    
    status_lines = ["🤖 Bot 所在群组列表:"]
    status_lines.append("=" * 30)
    
    for i, group_id in enumerate(all_groups, 1):
        status_lines.append(f"{i}. {group_id}")
    
    status_lines.append("=" * 30)
    status_lines.append(f"总计: {len(all_groups)} 个群组")
    
    message = "\n".join(status_lines)
    await app.send_message(group, MessageChain(Plain(message)))

@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                FullMatch("/config"),
                "args" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
            )
        ],
    )
)
async def config_group_available_modules_command(app: Ariadne, group: Group, member: Member, args: RegexResult):
    """Handle all /config commands with different argument patterns.
       /config 群组ID - 查看模块状态
       /config 群组ID all_on/all_off - 开启/关闭所有模块
       /config 群组ID 模块名 on/off - 设置模块状态
    """
    admin_group_id = str(group.id)
    
    # Check if this is an admin group
    if admin_group_id not in ADMIN_GROUPS:
        await app.send_message(group, MessageChain(Plain("此命令仅限管理群组使用。")))
        return
    
    # Parse arguments
    if not args.matched:
        await app.send_message(group, MessageChain(Plain("使用格式:\n/config 群组ID - 查看模块状态\n/config 群组ID all_on/all_off - 开启/关闭所有模块\n/config 群组ID 模块名 on/off - 设置模块状态")))
        return
    
    arg_parts = args.result.display.strip().split()
    
    if len(arg_parts) == 1:
        # /config group_id - show status
        target_group_id = arg_parts[0]
        
        # Validate target group exists
        all_groups = await get_all_groups(app)
        if target_group_id not in all_groups:
            await app.send_message(group, MessageChain(Plain(f"群组 '{target_group_id}' 不存在或bot不在该群组中。")))
            return
        
        available_modules = get_available_modules()
        
        # Build status message for specific group
        status_lines = [f"🤖 群组 {target_group_id} 模块状态:"]
        status_lines.append("=" * 40)
        status_lines.append("")
        
        for module in available_modules:
            enabled = module_config_manager.is_module_enabled(target_group_id, module)
            status = "✅" if enabled else "❌"
            status_lines.append(f"  {status} {module}")
        
        status_lines.append("")
        status_lines.append("=" * 40)
        status_lines.append("使用格式:")
        status_lines.append(f"/config {target_group_id} 模块名 on/off")
        status_lines.append(f"/config {target_group_id} all_on")
        status_lines.append(f"/config {target_group_id} all_off")
        
        message = "\n".join(status_lines)
        await app.send_message(group, MessageChain(Plain(message)))
        
    elif len(arg_parts) == 2:
        # /config group_id all_on/all_off
        target_group_id = arg_parts[0]
        action_str = arg_parts[1].lower()
        
        # Validate action
        if action_str not in ["all_on", "all_off"]:
            await app.send_message(group, MessageChain(Plain("无效操作。使用 'all_on' 或 'all_off'")))
            return
        
        # Validate target group exists
        all_groups = await get_all_groups(app)
        if target_group_id not in all_groups:
            await app.send_message(group, MessageChain(Plain(f"群组 '{target_group_id}' 不存在或bot不在该群组中。")))
            return
        
        # Get all available modules
        available_modules = get_available_modules()
        
        # Set all modules status
        enabled = action_str == "all_on"
        for module_name in available_modules:
            module_config_manager.set_module_status(target_group_id, module_name, enabled)
        
        status_emoji = "✅" if enabled else "❌"
        action_text = "全部开启" if enabled else "全部关闭"
        await app.send_message(group, MessageChain(Plain(f"群组 {target_group_id} 的所有模块已设置为 {status_emoji} {action_text}")))
        
    elif len(arg_parts) == 3:
        # /config group_id module_name on/off
        target_group_id = arg_parts[0]
        module_name = arg_parts[1]
        status_str = arg_parts[2].lower()
        
        # Validate status
        if status_str not in ["on", "off"]:
            await app.send_message(group, MessageChain(Plain("状态必须是 'on' 或 'off'")))
            return
        
        # Validate module exists
        available_modules = get_available_modules()
        if module_name not in available_modules:
            await app.send_message(group, MessageChain(Plain(f"模块 '{module_name}' 不存在。\n可用模块: {', '.join(available_modules)}")))
            return
        
        # Validate target group exists
        all_groups = await get_all_groups(app)
        if target_group_id not in all_groups:
            await app.send_message(group, MessageChain(Plain(f"群组 '{target_group_id}' 不存在或bot不在该群组中。")))
            return
        
        # Set module status
        enabled = status_str == "on"
        module_config_manager.set_module_status(target_group_id, module_name, enabled)
        
        status_emoji = "✅" if enabled else "❌"
        await app.send_message(group, MessageChain(Plain(f"群组 {target_group_id} 的模块 '{module_name}' 已设置为 {status_emoji} {'开启' if enabled else '关闭'}")))
        
    else:
        await app.send_message(group, MessageChain(Plain("参数数量错误。使用格式:\n/config 群组ID\n/config 群组ID all_on/all_off\n/config 群组ID 模块名 on/off")))

@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(FullMatch("/admin"))],
    )
)
async def admin_command(app: Ariadne, group: Group, member: Member):
    """Handle /admin command to show admin group status"""
    group_id = str(group.id)
    
    is_admin = group_id in ADMIN_GROUPS
    
    message = f"当前群组 {group_id} {'是' if is_admin else '不是'} 管理群组"
    if is_admin:
        message += "\n管理员命令:\n/groups - 查看所有群组列表\n/config 群组ID - 查看指定群组模块状态\n/config 群组ID 模块名 on/off - 设置模块状态\n/config 群组ID all_on/all_off - 开启/关闭所有模块"
    else:
        message += "\n如需管理模块配置，请联系bot管理员将此群组设置为管理群组"
    
    await app.send_message(group, MessageChain(Plain(message)))


# Get all available modules
def get_available_modules():
    """Get list of all available modules"""
    modpath = os.getcwd() + '/modules'
    modules = []
    for f in os.listdir(modpath):
        if os.path.isfile(os.path.join(modpath, f)) and f.endswith('.py') and f != 'config_manager.py':
            module_name = f.split('.', 1)[0]
            modules.append(module_name)
    return sorted(modules)

async def get_all_groups(app: Ariadne):
    """Get all groups the bot is currently in"""
    try:
        group_list = await app.get_group_list()
        return [str(group.id) for group in group_list]
    except Exception as e:
        logger.error(f"Failed to get group list: {e}")
        return []