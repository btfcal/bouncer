"""
BTF Bouncer on-boarding bot
Written by Mingjie Jiang <m6@berkeley.edu>
"""

import os
from enum import Enum
import discord
from discord.ext import commands
from datetime import datetime
import utils as utils
import re
import asyncio
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from python_http_client.exceptions import HTTPError

# load environment variables
from dotenv import load_dotenv
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')

# configuration variables
PENDING_ROLE_ID = int(os.getenv('PENDING_ROLE_ID'))
MEMBER_ROLE_ID = int(os.getenv('MEMBER_ROLE_ID'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
VERIFICATION_CATEGORY_ID = int(os.getenv('VERIFICATION_CATEGORY_ID'))
VALID_DOMAIN = os.getenv("VALID_DOMAIN")
SUPPORT_ROLE_ID = int(os.getenv('SUPPORT_ROLE_ID'))

# initialize discord
intents = intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

WATCH_SOS = []  # array of messages to watch out for SOS from


class Status(Enum):
    info = discord.Color.blue()
    success = discord.Color.green()
    warning = discord.Color.gold()
    error = discord.Color.red()
    unknown = discord.Color.light_gray()


async def spit_log(
        msg,
        title=f"New Log - {datetime.now().astimezone().strftime('%d/%m/%Y %H:%M:%S %Z')}",
        status=Status.unknown):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    # spits a line of log in the logging channel
    if msg:
        embedded_message = discord.Embed(title=title,
                                         description=msg,
                                         color=status.value)
        log_message = await log_channel.send(embed=embedded_message)
        return log_message

    return


async def pause(channel, seconds):
    async with channel.typing():
        await asyncio.sleep(seconds)


def valid_email(str):
    regex = "(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
    return re.search(regex, str)

async def init_onboard(member):
    # initialize onboarding procedure
    guild = member.guild
    code = utils.random_string()

    # 1. assign pending role
    pending_role = discord.utils.get(guild.roles, id=PENDING_ROLE_ID)
    await member.add_roles(pending_role)
    await spit_log(
        f'{member.mention} pending role assigned. Executing onboarding flow.',
        title=f"⏬ Starting to onboard {member.name}... Step 1 complete!",
        status=Status.success)

    # 2. create and assign temp role & channel
    onboard_role = await guild.create_role(name="o-" + code)
    await member.add_roles(onboard_role)
    channel_config_overwrites = {
        guild.default_role:
        discord.PermissionOverwrite(view_channel=False),
        pending_role:
        discord.PermissionOverwrite(view_channel=False),
        onboard_role:
        discord.PermissionOverwrite(view_channel=True,
                                    read_messages=True,
                                    send_messages=True)
    }
    verification_category = discord.utils.get(guild.categories,
                                              id=VERIFICATION_CATEGORY_ID)
    onboard_channel = await guild.create_text_channel(
        name=code,
        category=verification_category,
        overwrites=channel_config_overwrites)
    await spit_log(f'Role {code} created and assigned for {member.mention}.',
                   title=f"⏬ Onboarding {member.name}... Step 2 complete!",
                   status=Status.success)

    # 3. send welcome messages
    welcome_message = await onboard_channel.send(
        f'Welcome to **Build the Future Community**, {member.mention}! ' +
        'This is your personal onboarding channel. I\'m Bouncer, the gatekeeper for BTF, and I will be guiding you through the process.'
        + '\n\nIf at any time, you feel like something is not working, ' +
        'please come back to this message and click the 🆘 button, and a staff member will be on their way to help you! '
        + '\n\n(Click the :wave: below to begin!)')
    await welcome_message.add_reaction('👋')
    await welcome_message.add_reaction('🆘')

    WATCH_SOS.append(welcome_message)

    def check_welcome(reaction, user):
        return user == member and str(reaction.emoji) == '👋'

    welcome_pending_log = await spit_log(
        f'{member.mention} ready to start onboarding. Waiting for reaction...',
        title=f"⏸ Onboarding {member.name}... Step 3 pending...",
        status=Status.warning)

    await bot.wait_for('reaction_add', check=check_welcome)
    await onboard_channel.send('Waving back at ya! 👋 One second...')

    await welcome_pending_log.delete()

    await spit_log(f'{member.mention} onboarding started!',
                   title=f"⏬ Onboarding {member.name}... Step 3 complete!",
                   status=Status.success)

    await pause(onboard_channel, 2)
    await onboard_channel.send(
        'In order to allow you to enter our Discord community, we need to complete a few quick onboarding steps...'
    )
    await pause(onboard_channel, 1)
    await onboard_channel.send(
        'First, please read our **Code of Conduct**. Breaking any rules in the Code of Conduct will result in your prompt removal from the BTF Community.'
    )
    await pause(onboard_channel, 1)
    await onboard_channel.send(
        'https://docs.google.com/document/d/1H9ammGSeypqZufuMT3Qn8Lcb-gBPxxoZ3PjDrDcUZis/edit'
    )
    await pause(onboard_channel, 2)
    await onboard_channel.send(
        '**Please respond with `agree` to acknowledge the Code of Conduct.**')

    # 4. wait for acknowledgement on CoC
    def check_coc(m):
        return "agree" in m.content.lower() and m.channel == onboard_channel

    coc_pending_log = await spit_log(
        f'Conduct agreement sent to the welcome channel for {member.mention}. Awaiting acknowledgement...',
        title=f"⏸ Onboarding {member.name}... Step 4 pending...",
        status=Status.warning)

    coc_pending = await bot.wait_for('message', check=check_coc)
    await onboard_channel.send(
        f"Thank you for your agreement, {member.name}!".format(coc_pending))
    await coc_pending_log.delete()

    await spit_log(f'Conduct acknowledged by {member.mention}!',
                   title=f"⏬ Onboarding {member.name}... Step 4 complete!",
                   status=Status.success)

    # 5. wait for email address
    await pause(onboard_channel, 2)
    await onboard_channel.send('Now, we need to verify your email address.')
    email_pending_log = await spit_log(
        f'Email prompt sent to the welcome channel for {member.mention}. Awaiting email...',
        title=f"⏸ Onboarding {member.name}... Step 5 pending...",
        status=Status.warning)

    async def email_check_bump():
        """
      Stuck user in this loop until a valid email is provided
      """
        await pause(onboard_channel, 1)
        await onboard_channel.send(
            '**Please reply here with your @berkeley.edu email address.**')

        email_pending = await bot.wait_for(
            'message', check=lambda m: m.channel == onboard_channel)
        return email_pending.content

    email = await email_check_bump()

    def valid_domain(str):
        return str.endswith(VALID_DOMAIN)

    while not (valid_email(email) and valid_domain(email)):
        """
      Stuck user in this loop until a valid email is provided
      """
        if not valid_email(email):
            await onboard_channel.send(
                '**Invalid response** - are you sure this is an email?')
        elif not valid_domain(email):
            await onboard_channel.send(
                f'**Invalid domain.** Your email must end with {VALID_DOMAIN}.'
            )

        email = await email_check_bump()
    await email_pending_log.delete()

    await spit_log(f'Email collected from {member.mention}: {email}',
                   title=f"⏬ Onboarding {member.name}... Step 5 complete!",
                   status=Status.success)

    # generate random code
    code = random.randint(100000, 999999)
    send_code(email, code)
    await onboard_channel.send(
        f'Go Bears! :bear: We just sent an email to **{email}**!')
    code_pending_log = await spit_log(
        f'Verification code {str(code)} sent to {member.mention} at {email}. Awaiting user code input...',
        title=f"⏸ Onboarding {member.name}... Step 6 pending...",
        status=Status.warning)

    async def code_check_bump():
        """
      Stuck user in this loop until a valid code is provided
      """
        await pause(onboard_channel, 1)
        await onboard_channel.send(
            '**Please reply here with the 6-digit code.**')

        email_pending = await bot.wait_for(
            'message', check=lambda m: m.channel == onboard_channel)
        return email_pending.content

    user_code = await code_check_bump()

    while not user_code == str(code):
        await onboard_channel.send(
            'Incorrect code! Try again? (If you are stuck here, don\'t be afraid to hit the SOS reaction on the first messsage of this channel to request help!)'
        )
        user_code = await code_check_bump()

    await code_pending_log.delete()

    await spit_log(f'{member.mention} email {email} verified successfully!',
                   title=f"⏬ Onboarding {member.name}... Step 6 complete!",
                   status=Status.success)

    # onboarding complete
    WATCH_SOS.remove(welcome_message)
    await spit_log(f'{member.mention} removed from SOS watchlist.',
                   title=f"✅ {member.name} Onboarding Complete!",
                   status=Status.success)

    await onboard_channel.send(
        '🎉 Verification complete! Be sure to reach out to staff if you have any questions!'
    )
    complete_message = await onboard_channel.send('React 👍 to this message to clean up this channel and unlock the rest of the community.')
    await complete_message.add_reaction('👍')

    def check_cleanup(reaction, user):
        return user == member and str(reaction.emoji) == '👍'

    await bot.wait_for('reaction_add', check=check_cleanup)

    await onboard_role.delete()
    await onboard_channel.delete()

    await spit_log(f'{member.mention} onboarding role and channel deleted.',
                   title=f"🧼 {member.name} Onboarding Cleaned Up!",
                   status=Status.success)

    member_role = discord.utils.get(guild.roles, id=MEMBER_ROLE_ID)
    await member.add_roles(member_role)


def send_code(email, code):
    print('Sending email to', email, 'with code', code)
    message = Mail(from_email='btf@orph.app', to_emails=[email])

    data = {'code': str(code)}

    message.dynamic_template_data = data
    message.template_id = os.getenv('SENDGRID_TEMPLATE')

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_KEY'))
        sg.send(message)
        print("Dynamic Messages Sent!")
    except HTTPError as e:
        print(e.to_dict)


@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.id == GUILD_ID:
            break

    # Debugging Area - Remove For Production
    await spit_log(f'{bot.user} has connected to Discord & guild {guild.name}!'
                   )


@bot.event
async def on_member_join(member):
    await spit_log(f'Say welcome to {member.name}!',
                   title="👋 New member joined!",
                   status=Status.info)
    await init_onboard(member)


@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    if message in WATCH_SOS and reaction.emoji == "🆘" and user != bot.user:
        # SOS received, inviting staff
        support_role = discord.utils.get(user.guild.roles, id=SUPPORT_ROLE_ID)
        await message.channel.send(
            f"Help requested! A staff member will be here to help you soon. {support_role.mention}"
        )
        await spit_log(
            f'{user.name} just requested help in {message.channel.mention}!',
            title=f"🆘 Help requested by {user.name}!",
            status=Status.error)
        WATCH_SOS.remove(message)
        await message.channel.set_permissions(support_role, view_channel=True)
    pass


@bot.command()
@commands.has_role('staff')
async def onboard(ctx, *, member: discord.Member):
    """
    Manually start the onboarding flow of a user
    """
    await spit_log(f'Say welcome to {member.name}!',
                   title="👋 New member joined!",
                   status=Status.info)
    await init_onboard(member)


@bot.command()
@commands.has_role('staff')
async def reset_server(ctx):
    """
    Reset the server to initial state, clear out all 
    - Onboarding-created roles
    - Onboarding-created channels
    """

    # Delete onboarding-created roles
    removed_roles = []
    for role in ctx.guild.roles:
        if role.name.startswith("o-"):
            try:
                await role.delete()
                removed_roles.append(role.name)
            except discord.Forbidden:
                await spit_log(f'The role {role.name} cannot be removed!',
                               status=Status.error)

    if len(removed_roles) > 0:
        await spit_log(f'Roles {", ".join(removed_roles)} have been swept up!',
                       status=Status.success)
    else:
        await spit_log(f'No roles were removed!', status=Status.info)

    # Delete onboarding-created channels
    removed_channels = []
    verification_category = discord.utils.get(ctx.guild.categories,
                                              id=VERIFICATION_CATEGORY_ID)
    for channel in verification_category.channels:
        await channel.delete()
        removed_channels.append(channel.name)

    if len(removed_channels) > 0:
        await spit_log(
            f'Channels {", ".join(removed_channels)} have been swept up!',
            status=Status.success)
    else:
        await spit_log(f'No channels were removed!', status=Status.info)

@bot.command()
@commands.has_role('staff')
async def email_code(ctx, email, code):
  if not valid_email(email):
    await ctx.send('{} is not a valid email address.'.format(email))

  send_code(email, code)
  await ctx.send('Successfully sent code {} to {}.'.format(code, email))

bot.run(DISCORD_TOKEN)
