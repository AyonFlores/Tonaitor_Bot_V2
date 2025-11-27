# utils/ui.py
import discord
import re


# --- HELPER ---
def clean_and_truncate(text, url, limit=1000):
    if not text: return "No description available."
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text).replace("  ", " ").strip()
    if len(text) > limit:
        return f"{text[:limit]}... [(Read More on Website)]({url})"
    return text


# --- EMBED BUILDERS ---
def build_media_embed(media):
    title = media['title']['english'] or media['title']['romaji']
    color_hex = media['coverImage']['color']
    embed_color = int(color_hex.replace("#", ""), 16) if color_hex else 0x3498db

    desc = clean_and_truncate(media['description'], media['siteUrl'])

    embed = discord.Embed(
        title=f"{title} ({media['startDate']['year']})",
        url=media['siteUrl'],
        description=desc,
        color=embed_color
    )

    # Image Layout: Poster is Big (Bottom), Banner is Thumbnail (Top Right)
    if media['bannerImage']:
        embed.set_image(url=media['bannerImage'])
        embed.set_thumbnail(url=media['coverImage']['extraLarge'])
    else:
        embed.set_image(url=media['coverImage']['extraLarge'])

    # Fields
    score = f"{media['averageScore']}%" if media['averageScore'] else "N/A"
    status = media['status'].title().replace("_", " ") if media['status'] else "Unknown"

    studios = "Unknown"
    if media.get('studios') and media['studios']['nodes']:
        studios = ", ".join([s['name'] for s in media['studios']['nodes']])

    embed.add_field(name="⭐ Score", value=score, inline=True)

    if media.get('episodes') is not None:
        embed.add_field(name="🏢 Studio", value=studios, inline=True)
        embed.add_field(name="📺 Episodes", value=str(media['episodes']), inline=True)
    elif media.get('chapters') is not None:
        embed.add_field(name="📚 Volumes", value=str(media['volumes'] or "?"), inline=True)
        embed.add_field(name="📑 Chapters", value=str(media['chapters'] or "?"), inline=True)

    embed.add_field(name="📅 Status", value=status, inline=True)

    if media['genres']:
        embed.add_field(name="🎭 Genres", value=", ".join(media['genres'][:3]), inline=True)

    # Related
    relations = media.get('relations', {}).get('edges', [])
    related_lines = []
    for edge in relations:
        if edge['relationType'] in ["ADAPTATION", "PREQUEL", "SEQUEL"]:
            node = edge['node']
            if node:
                t = node['title']['english'] or node['title']['romaji']
                related_lines.append(f"[{t}]({node['siteUrl']}) ({edge['relationType'].title()})")

    if related_lines:
        embed.add_field(name="🎬 Related Media", value="\n".join(related_lines[:5]), inline=False)

    # Links
    links = media.get('externalLinks', [])
    if links:
        formatted = [f"[{l['site']}]({l['url']})" for l in links[:6]]
        embed.add_field(name="🔗 Links", value=" | ".join(formatted), inline=False)

    return embed


def build_character_embed(char):
    name = char['name']['full']
    desc = clean_and_truncate(char['description'], char['siteUrl'])

    embed = discord.Embed(title=name, url=char['siteUrl'], description=desc, color=0x9b59b6)

    if char['image']['large']:
        embed.set_image(url=char['image']['large'])

    embed.add_field(name="❤️ Favorites", value=f"{char['favourites']:,}", inline=True)

    media_nodes = char.get('media', {}).get('nodes', [])
    if media_nodes:
        lines = []
        for m in media_nodes:
            t = m['title']['english'] or m['title']['romaji']
            lines.append(f"• [{t}]({m['siteUrl']}) ({m['type'].title()})")
        embed.add_field(name="🎬 Appearances", value="\n".join(lines), inline=False)

    return embed


# --- PAGINATION ---
class PaginationView(discord.ui.View):
    def __init__(self, results, embed_factory, author_id):
        super().__init__(timeout=60)
        self.results = results
        self.embed_factory = embed_factory
        self.author_id = author_id
        self.current_page = 0

        if len(self.results) <= 1:
            self.children[0].disabled = True
            self.children[1].disabled = True

    async def update_view(self, interaction: discord.Interaction):
        data = self.results[self.current_page]
        embed = self.embed_factory(data)
        embed.set_footer(text=f"Result {self.current_page + 1} of {len(self.results)} • Powered by AniList GraphQL")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.results)
        await self.update_view(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.results)
        await self.update_view(interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This control is not for you!", ephemeral=True)
            return False
        return True