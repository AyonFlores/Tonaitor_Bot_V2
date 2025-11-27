# cogs/search.py
import discord
from discord.ext import commands
from utils.api import fetch_anilist, RateLimitError
# Import the new query and embed builder
from utils.queries import MEDIA_QUERY, CHARACTER_QUERY, USER_QUERY
from utils.ui import build_media_embed, build_character_embed, build_user_embed, PaginationView


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # (generic_search function remains unchanged)
    async def generic_search(self, interaction, name, query, type_var, embed_builder):
        await interaction.response.defer()

        variables = {'search': name}
        if type_var: variables['type'] = type_var

        try:
            data = await fetch_anilist(self.bot.session, query, variables)

            key = 'media' if 'media' in data['Page'] else 'characters'
            results = data['Page'].get(key)

            if results:
                view = PaginationView(results, embed_builder, interaction.user.id)
                embed = embed_builder(results[0])
                embed.set_footer(text=f"Result 1 of {len(results)} • Powered by AniList GraphQL")
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(f"No results found for '{name}'")

        except RateLimitError as e:
            await interaction.followup.send(f"⚠️ **API Rate Limit.** Wait {e.wait_time}s.")
        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("An error occurred.")

    @discord.app_commands.command(name="anime", description="Search for an anime")
    async def anime(self, interaction: discord.Interaction, anime_name: str):
        await self.generic_search(interaction, anime_name, MEDIA_QUERY, 'ANIME', build_media_embed)

    @discord.app_commands.command(name="manga", description="Search for a manga")
    async def manga(self, interaction: discord.Interaction, manga_name: str):
        await self.generic_search(interaction, manga_name, MEDIA_QUERY, 'MANGA', build_media_embed)

    @discord.app_commands.command(name="character", description="Search for a character")
    async def character(self, interaction: discord.Interaction, character_name: str):
        await self.generic_search(interaction, character_name, CHARACTER_QUERY, None, build_character_embed)

    # --- NEW COMMAND ---
    @discord.app_commands.command(name="user", description="Search for an AniList user profile")
    async def user(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        variables = {'name': username}

        try:
            # Users don't need pagination, so we don't use generic_search
            data = await fetch_anilist(self.bot.session, USER_QUERY, variables)

            if data and data.get('User'):
                user_data = data['User']
                embed = build_user_embed(user_data)
                embed.set_footer(text="Powered by AniList GraphQL")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"User '{username}' not found!")

        except RateLimitError as e:
            await interaction.followup.send(f"⚠️ **API Rate Limit.** Wait {e.wait_time}s.")
        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("An error occurred.")


async def setup(bot):
    await bot.add_cog(Search(bot))