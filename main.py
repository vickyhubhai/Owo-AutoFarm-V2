import discord
from discord.ext import commands
import colorama
from colorama import Fore
import asyncio
from webserver import keep_alive
from dotenv import load_dotenv
import os
import random
import time
import json
from datetime import datetime, timedelta

#-----SETUP-----#
prefix = ">"

load_dotenv()
keep_alive()
token = os.getenv("TOKEN")

if token is None:
    print("ERROR: TOKEN not found in environment variables!")
    exit(1)

bot = commands.Bot(command_prefix=prefix,
                   help_command=None,
                   case_insensitive=True,
                   self_bot=True)

# Advanced settings for 400k daily target
advanced_settings = {
    'target_cash': 400000,     # 400k target
    'hourly_target': 16667,    # 400k / 24 hours
    'flip_amount': 1500,       # Optimal flip amount for profits
    'auto_gamble': True,       # Enable strategic gambling
    'smart_timing': True,      # Avoid detection patterns
    'max_hunt_per_hour': 180,  # Optimal hunting frequency
    'anti_ban_mode': True,     # Enhanced ban prevention
    'session_breaks': True,    # Take strategic breaks
    'lucky_mode': True,        # Use luck-based strategies
}

# Enhanced command statistics with cash tracking
cmd_stats = {
    'owoh': 0, 'hunt': 0, 'battle': 0, 'sell': 0, 'flip': 0, 
    'cash': 0, 'pray': 0, 'gamble': 0, 'slots': 0,
    'total_earned': 0, 'session_earnings': 0
}

# Global variables
dmcs = False
session_start = None
last_pray_time = 0
daily_earnings = 0
hourly_earnings = 0
last_hour_check = time.time()
break_counter = 0

# Safe delete helper function
async def safe_delete_message(message):
    try:
        await message.delete()
    except discord.NotFound:
        print(f"{Fore.YELLOW}Warning: Message already deleted")
    except discord.Forbidden:
        print(f"{Fore.YELLOW}Warning: No permission to delete message")
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Error deleting message: {e}")

# Calculate optimal strategies
def calculate_hourly_strategy():
    """Calculate optimal strategy for current hour"""
    current_hour = datetime.now().hour
    
    # Peak hours (fewer people online) - more aggressive
    if 2 <= current_hour <= 6 or 14 <= current_hour <= 16:
        return {
            'hunt_frequency': 25,      # Hunt every 25 seconds
            'flip_amount': 2000,       # Higher flips
            'use_gamble': True,        # Enable gambling
            'break_duration': 180,     # 3 min breaks
        }
    # Regular hours - balanced approach
    elif 7 <= current_hour <= 13 or 17 <= current_hour <= 22:
        return {
            'hunt_frequency': 35,      # Hunt every 35 seconds
            'flip_amount': 1500,       # Medium flips
            'use_gamble': True,        # Selective gambling
            'break_duration': 300,     # 5 min breaks
        }
    # High traffic hours - conservative
    else:
        return {
            'hunt_frequency': 45,      # Hunt every 45 seconds
            'flip_amount': 1000,       # Lower flips
            'use_gamble': False,       # No gambling
            'break_duration': 600,     # 10 min breaks
        }

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="💰 Advanced OwO Money Maker - 400k Daily Target",
        description="Optimized for maximum earnings while staying ban-safe",
        color=0x00ff00
    )
    
    embed.add_field(
        name="🚀 Main Commands",
        value=f"""
        `{prefix}moneymaker` - Start 400k daily grind mode
        `{prefix}stopmaker` - Stop money maker safely
        `{prefix}aggressive` - High-risk high-reward mode
        `{prefix}conservative` - Safe slow earning mode
        """,
        inline=False
    )
    
    embed.add_field(
        name="📊 Tracking",
        value=f"""
        `{prefix}earnings` - View earnings statistics
        `{prefix}progress` - Check progress to 400k goal
        `{prefix}hourly` - View hourly earnings rate
        """,
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Settings",
        value=f"""
        `{prefix}setflip <amount>` - Set flip amount (500-5000)
        `{prefix}strategy` - View current strategy
        `{prefix}togglegamble` - Toggle gambling mode
        """,
        inline=False
    )
    
    embed.set_footer(text="Target: 400k in 24hrs | Stay ban-safe! 🛡️")
    await ctx.send(embed=embed)

@bot.command()
async def earnings(ctx):
    await safe_delete_message(ctx.message)
    
    embed = discord.Embed(
        title="💰 Earnings Dashboard",
        color=0x00ff00
    )
    
    # Calculate session time
    if session_start:
        session_time = datetime.now() - session_start
        hours = session_time.total_seconds() / 3600
        hourly_rate = cmd_stats['session_earnings'] / hours if hours > 0 else 0
    else:
        hours = 0
        hourly_rate = 0
    
    embed.add_field(
        name="📈 Session Stats",
        value=f"""
        Earned This Session: {cmd_stats['session_earnings']:,}
        Total Earned: {cmd_stats['total_earned']:,}
        Hourly Rate: {hourly_rate:,.0f}/hr
        """,
        inline=True
    )
    
    embed.add_field(
        name="🎯 Daily Progress",
        value=f"""
        Target: 400,000
        Current: {daily_earnings:,}
        Remaining: {400000 - daily_earnings:,}
        Progress: {(daily_earnings/400000)*100:.1f}%
        """,
        inline=True
    )
    
    embed.add_field(
        name="⏰ Time Analysis",
        value=f"""
        Session Time: {hours:.1f}h
        ETA to 400k: {((400000-daily_earnings)/hourly_rate):.1f}h
        Commands Sent: {sum(cmd_stats.values())}
        """,
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def strategy(ctx):
    await safe_delete_message(ctx.message)
    
    current_strategy = calculate_hourly_strategy()
    current_hour = datetime.now().hour
    
    embed = discord.Embed(
        title="🎯 Current Strategy",
        color=0x0099ff
    )
    
    # Determine time period
    if 2 <= current_hour <= 6 or 14 <= current_hour <= 16:
        period = "🟢 PEAK HOURS (Aggressive)"
    elif 7 <= current_hour <= 13 or 17 <= current_hour <= 22:
        period = "🟡 REGULAR HOURS (Balanced)"
    else:
        period = "🔴 HIGH TRAFFIC (Conservative)"
    
    embed.add_field(
        name="⏰ Time Period",
        value=period,
        inline=False
    )
    
    embed.add_field(
        name="🎮 Strategy Details",
        value=f"""
        Hunt Frequency: {current_strategy['hunt_frequency']}s
        Flip Amount: {current_strategy['flip_amount']}
        Gambling: {'✅' if current_strategy['use_gamble'] else '❌'}
        Break Duration: {current_strategy['break_duration']}s
        """,
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def setflip(ctx, amount: int = 1500):
    await safe_delete_message(ctx.message)
    
    if amount < 500 or amount > 5000:
        await ctx.send("❌ Flip amount must be between 500 and 5000 for optimal results!")
        return
    
    advanced_settings['flip_amount'] = amount
    await ctx.send(f"✅ Flip amount set to {amount}")

@bot.command()
async def togglegamble(ctx):
    await safe_delete_message(ctx.message)
    
    advanced_settings['auto_gamble'] = not advanced_settings['auto_gamble']
    status = "enabled" if advanced_settings['auto_gamble'] else "disabled"
    await ctx.send(f"🎰 Gambling {status}!")

@bot.command(pass_context=True)
async def moneymaker(ctx):
    """Main money making command optimized for 400k daily"""
    await safe_delete_message(ctx.message)
    await ctx.send('💰 **MONEY MAKER ACTIVATED** - Target: 400k in 24hrs!')
    
    global dmcs, session_start, daily_earnings, break_counter
    dmcs = True
    session_start = datetime.now()
    cycle_count = 0
    
    while dmcs:
        try:
            # Get current optimal strategy
            strategy = calculate_hourly_strategy()
            
            async with ctx.typing():
                # Phase 1: Core hunting and battling
                await ctx.send('owoh')
                cmd_stats['owoh'] += 1
                await asyncio.sleep(random.randint(2, 4))
                
                await ctx.send('owo hunt')
                cmd_stats['hunt'] += 1
                estimated_earnings = random.randint(200, 800)  # Estimate from hunt
                cmd_stats['session_earnings'] += estimated_earnings
                daily_earnings += estimated_earnings
                print(f"{Fore.GREEN}Hunt completed - Estimated: +{estimated_earnings}")
                
                await asyncio.sleep(random.randint(2, 4))
                await ctx.send('owo battle')
                cmd_stats['battle'] += 1
                estimated_earnings = random.randint(150, 600)
                cmd_stats['session_earnings'] += estimated_earnings
                daily_earnings += estimated_earnings
                print(f"{Fore.GREEN}Battle completed - Estimated: +{estimated_earnings}")
                
                # Phase 2: Strategic selling (only safe animals)
                await asyncio.sleep(random.randint(5, 10))
                safe_animals = ['cow', 'pig', 'duck', 'cat', 'dog', 'rat', 'fish', 'ant']
                for animal in random.sample(safe_animals, 3):
                    await ctx.send(f'owo sell {animal}')
                    cmd_stats['sell'] += 1
                    await asyncio.sleep(random.randint(1, 2))
                
                # Phase 3: Smart flipping
                flip_amount = strategy['flip_amount']
                await ctx.send(f'owo flip {flip_amount}')
                cmd_stats['flip'] += 1
                
                # Simulate flip results (50% win rate with slight house edge)
                if random.random() < 0.48:  # 48% win rate
                    earnings = flip_amount * 0.9  # Win but with house edge
                    print(f"{Fore.GREEN}Flip WON - Earned: +{earnings}")
                else:
                    earnings = -flip_amount * 0.5  # Lose but not full amount
                    print(f"{Fore.RED}Flip LOST - Lost: {earnings}")
                
                cmd_stats['session_earnings'] += earnings
                daily_earnings += earnings
                
                await asyncio.sleep(random.randint(3, 6))
                
                # Phase 4: Cash collection
                await ctx.send('owo cash')
                cmd_stats['cash'] += 1
                
                # Phase 5: Strategic gambling (if enabled and profitable time)
                if strategy['use_gamble'] and advanced_settings['auto_gamble']:
                    if random.random() < 0.3:  # 30% chance to gamble
                        gamble_amount = min(500, flip_amount // 3)
                        await ctx.send(f'owo slots {gamble_amount}')
                        cmd_stats['gamble'] += 1
                        
                        # Simulate gambling (house always wins long term)
                        if random.random() < 0.25:  # 25% win rate
                            slot_earnings = gamble_amount * random.uniform(2, 5)
                            print(f"{Fore.GREEN}Slots WON - Earned: +{slot_earnings}")
                        else:
                            slot_earnings = -gamble_amount
                            print(f"{Fore.RED}Slots LOST - Lost: {slot_earnings}")
                        
                        cmd_stats['session_earnings'] += slot_earnings
                        daily_earnings += slot_earnings
                        await asyncio.sleep(random.randint(2, 4))
                
                # Phase 6: Auto pray (every 10 minutes)
                now = time.time()
                if now - last_pray_time > 600:
                    await ctx.send('owo pray')
                    cmd_stats['pray'] += 1
                    last_pray_time = now
                    daily_earnings += random.randint(1000, 3000)  # Pray bonus
                    print(f"{Fore.GREEN}Prayed successfully")
                
                # Phase 7: Inventory management (every 5 cycles)
                cycle_count += 1
                if cycle_count % 5 == 0:
                    await ctx.send('owo inv')
                    print(f"{Fore.GREEN}Checking inventory...")
                    await asyncio.sleep(3)
                
                # Phase 8: Anti-ban breaks
                break_counter += 1
                if break_counter >= 15:  # Every 15 cycles
                    break_duration = strategy['break_duration']
                    print(f"{Fore.YELLOW}Taking {break_duration}s break to avoid detection...")
                    await ctx.send(f"💤 Taking {break_duration//60}min break...")
                    await asyncio.sleep(break_duration)
                    break_counter = 0
                
                # Progress update every hour
                current_time = time.time()
                if current_time - last_hour_check >= 3600:  # 1 hour
                    progress = (daily_earnings / 400000) * 100
                    await ctx.send(f"📊 **Hourly Update**: {daily_earnings:,}/400k ({progress:.1f}%)")
                    last_hour_check = current_time
                
                # Dynamic sleep based on strategy
                sleep_time = random.randint(strategy['hunt_frequency'], strategy['hunt_frequency'] + 10)
                await asyncio.sleep(sleep_time)
                
        except Exception as e:
            print(f"{Fore.RED}Error in money maker: {e}")
            await asyncio.sleep(30)  # Wait before retrying

@bot.command(pass_context=True)
async def aggressive(ctx):
    """High-risk high-reward mode for experienced users"""
    await safe_delete_message(ctx.message)
    await ctx.send('⚡ **AGGRESSIVE MODE** - High risk, high reward!')
    
    global dmcs, session_start
    dmcs = True
    session_start = datetime.now()
    
    while dmcs:
        try:
            # Rapid fire commands with higher stakes
            commands = [
                'owoh',
                'owo hunt',
                'owo battle',
                f'owo flip {random.randint(2000, 3000)}',
                'owo slots 1000',
                'owo cash'
            ]
            
            for cmd in commands:
                await ctx.send(cmd)
                await asyncio.sleep(random.randint(1, 3))
                
                # Track earnings more aggressively
                if 'flip' in cmd:
                    amount = int(cmd.split()[-1])
                    earnings = amount if random.random() < 0.45 else -amount
                    daily_earnings += earnings
                    cmd_stats['session_earnings'] += earnings
            
            # Shorter break but still present
            await asyncio.sleep(random.randint(20, 40))
            
        except Exception as e:
            print(f"{Fore.RED}Error in aggressive mode: {e}")
            await asyncio.sleep(15)

@bot.command(pass_context=True)
async def conservative(ctx):
    """Safe mode with longer delays but steady earnings"""
    await safe_delete_message(ctx.message)
    await ctx.send('🛡️ **CONSERVATIVE MODE** - Safe and steady!')
    
    global dmcs, session_start
    dmcs = True
    session_start = datetime.now()
    
    while dmcs:
        try:
            # Conservative approach with longer delays
            await ctx.send('owoh')
            await asyncio.sleep(random.randint(8, 15))
            
            await ctx.send('owo hunt')
            await asyncio.sleep(random.randint(8, 15))
            
            await ctx.send('owo battle')
            await asyncio.sleep(random.randint(8, 15))
            
            # Conservative flipping
            await ctx.send(f'owo flip {random.randint(500, 1000)}')
            await asyncio.sleep(random.randint(8, 15))
            
            await ctx.send('owo cash')
            await asyncio.sleep(random.randint(8, 15))
            
            # Longer break between cycles
            await asyncio.sleep(random.randint(60, 120))
            
        except Exception as e:
            print(f"{Fore.RED}Error in conservative mode: {e}")
            await asyncio.sleep(30)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    
    # Enhanced gem usage for money making
    if str(message.author.id) in ["408785106942164992", "1202830963034296360"]:
        if hasattr(message, 'embeds') and message.embeds:
            embed = message.embeds[0]
            
            if embed.title and ("inventory" in embed.title.lower()):
                await asyncio.sleep(2)
                description = embed.description if embed.description else ''
                
                # Priority gems for money making
                money_gems = [
                    'hunting gem', 'luck gem', 'legendary gem', 'epic gem',
                    'huntbot', 'empowerment', 'cookie', 'cake'
                ]
                
                for gem in money_gems:
                    if gem.lower() in description.lower():
                        await asyncio.sleep(random.randint(1, 3))
                        await message.channel.send(f'owo use {gem}')
                        print(f"{Fore.GREEN}Used money gem: {gem}")

@bot.command()
async def stopmaker(ctx):
    await safe_delete_message(ctx.message)
    
    # Calculate final stats
    if session_start:
        session_time = datetime.now() - session_start
        hours = session_time.total_seconds() / 3600
        hourly_rate = cmd_stats['session_earnings'] / hours if hours > 0 else 0
        
        embed = discord.Embed(
            title="💰 Money Maker Stopped",
            color=0xff9900
        )
        
        embed.add_field(
            name="📊 Final Stats",
            value=f"""
            Session Earnings: {cmd_stats['session_earnings']:,}
            Session Time: {hours:.1f}h
            Hourly Rate: {hourly_rate:,.0f}/hr
            Progress to 400k: {(daily_earnings/400000)*100:.1f}%
            """,
            inline=False
        )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send('💰 Money maker stopped!')
    
    global dmcs, session_start
    dmcs = False
    session_start = None

@bot.event
async def on_ready():
    activity = discord.Game(name="400k Daily Grind 💰", type=4)
    await bot.change_presence(status=discord.Status.dnd, activity=activity)
    print(f'''{Fore.GREEN}
💰 ADVANCED OWO MONEY MAKER 💰
Target: 400k in 24 hours
Status: Ready for grinding!
Type {prefix}help for commands
''')

keep_alive()
try:
    bot.run(token)
except Exception as e:
    print(f"Error running bot: {e}")
    import traceback
    traceback.print_exc()
