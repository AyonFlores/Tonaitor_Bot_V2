# utils/ui.py
import discord
import re

# --- CONFIGURATION ---
GENRE_EMOJIS = {
    "Action": "💥",
    "Adventure": "🧭",
    "Comedy": "🤡",
    "Drama": "🎭",
    "Ecchi": "🍑",
    "Fantasy": "🏰",
    "Horror": "👻",
    "Mahou Shoujo": "💫",
    "Mecha": "🤖",
    "Music": "🎵",
    "Mystery": "🔎",
    "Psychological": "🧠",
    "Romance": "💖",
    "Sci-Fi": "🛸",
    "Slice of Life": "🍰",
    "Sports": "⚽",
    "Supernatural": "🔮",
    "Thriller": "🚨"
    # Fallback for others will be a standard white square ⬜
}

# --- HELPER ---
def clean_and_truncate(text, url=None, limit=1000):
    if not text:
        return "No description available."

    clean = re.compile('<.*?>|__|~{2,}|\*\*|\[|\]|\(.*?\)')
    text = re.sub(clean, '', text)
    text = text.replace("  ", " ").strip()

    if len(text) > limit:
        if url:
            return f"{text[:limit]}... [(Read More)]({url})"
        else:
            return f"{text[:limit]}..."
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

    if media['bannerImage']:
        embed.set_image(url=media['bannerImage'])
        embed.set_thumbnail(url=media['coverImage']['extraLarge'])
    else:
        embed.set_image(url=media['coverImage']['extraLarge'])

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


def build_user_embed(user):
    name = user['name']
    bio = clean_and_truncate(user['about'], limit=300)

    embed = discord.Embed(title=name, url=user['siteUrl'], description=bio, color=0x3DB4F2)

    if user['avatar']['large']:
        embed.set_thumbnail(url=user['avatar']['large'])

    if user['bannerImage']:
        embed.set_image(url=user['bannerImage'])

    asts = user['statistics']['anime']
    days_watched = f"{asts['minutesWatched'] / 60 / 24:.1f}" if asts['minutesWatched'] else "0"

    msts = user['statistics']['manga']

    embed.add_field(name="📺 Anime Stats",
                    value=f"**Count:** {asts['count']}\n**Episodes:** {asts['episodesWatched']}\n**Days:** {days_watched}",
                    inline=True)

    embed.add_field(name="📚 Manga Stats",
                    value=f"**Count:** {msts['count']}\n**Chapters:** {msts['chaptersRead']}\n**Volumes:** {msts['volumesRead']}",
                    inline=True)

    # --- GENRE OVERVIEW ---
    genres = asts.get('genres', [])
    if genres:
        genre_lines = []
        # Enforce max 4 genres, even if the query returns more
        for g in genres[:4]:
            g_name = g['genre']
            count = g['count']
            emoji = GENRE_EMOJIS.get(g_name, "⬜")
            genre_lines.append(f"{emoji} **{g_name}** - {count} Entries")

        embed.add_field(name="🎬 Favorite Genres", value="\n".join(genre_lines), inline=False)

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