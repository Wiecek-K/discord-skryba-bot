# bot/github_handler.py
import re
import traceback
from datetime import datetime
import discord
from github import Github, Auth, GithubException, GithubIntegration
# --- ZMIANA IMPORTÓW ---
import config

async def create_github_pull_request(payload: dict, interaction: discord.Interaction):
    """
    Tworzy Pull Request w repozytorium GitHub na podstawie danych z Discorda.
    """
    try:
        print(f"LOG [GitHub]: Rozpoczynam proces tworzenia Pull Requestu dla '{payload['proposer_name']}'...")
        auth = Auth.AppAuth(config.GITHUB_APP_ID, config.GITHUB_APP_PRIVATE_KEY)
        gi = GithubIntegration(auth=auth)
        owner, repo_slug = config.GITHUB_REPO_NAME.split('/')
        installation = gi.get_repo_installation(owner=owner, repo=repo_slug)
        g = installation.get_github_for_installation()
        repo = g.get_repo(config.GITHUB_REPO_NAME)
        print(f"LOG [GitHub]: Pomyślnie uwierzytelniono i uzyskano dostęp do repozytorium.")

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        proposer_sanitized = re.sub(r'[^a-zA-Z0-9-]', '', payload['proposer_name']).lower()
        new_branch_name = f"proposal/{proposer_sanitized}-{timestamp}"
        
        source_branch = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=source_branch.commit.sha)
        print(f"LOG [GitHub]: Utworzono gałąź '{new_branch_name}'.")

        file_path = f"{payload['channel_name']}/linki.md"
        try:
            file_content_obj = repo.get_contents(file_path, ref="main")
            current_content = file_content_obj.decoded_content.decode('utf-8')
            file_sha = file_content_obj.sha
        except GithubException as e:
            if e.status == 404:
                print(f"LOG [GitHub]: Plik '{file_path}' nie istnieje. Tworzenie nowego.")
                current_content = "| Link | Opis |\n|---|---|"
                file_sha = None
            else:
                raise

        sanitized_description = payload['description'].replace('\r\n', ' ').replace('\n', ' ').replace('|', '')
        link_title = payload['url'][:30] + ('...' if len(payload['url']) > 30 else '')
        new_row = f"| [{link_title}]({payload['url']}) | {sanitized_description} |"
        final_content = current_content.strip() + '\n' + new_row
        commit_message = f"feat: Dodaje propozycję od {payload['proposer_name']}"

        if file_sha:
            repo.update_file(file_path, commit_message, final_content, file_sha, branch=new_branch_name)
        else:
            repo.create_file(file_path, commit_message, final_content, branch=new_branch_name)
        print(f"LOG [GitHub]: Zapisano zmiany w gałęzi '{new_branch_name}'.")

        pr_title = f"Propozycja od {payload['proposer_name']}: {payload['url']}"
        pr_body = f"Nowa propozycja do bazy wiedzy dodana przez **@{payload['proposer_name']}**."
        pr = repo.create_pull(title=pr_title, body=pr_body, head=new_branch_name, base="main")
        print(f"LOG [GitHub]: Utworzono Pull Request #{pr.number}")

        await interaction.followup.send(content=f"Gotowe! Twoja propozycja czeka na akceptację: {pr.html_url}", ephemeral=True)
    except Exception as e:
        print(f"KRYTYCZNY BŁĄD [GitHub]: Wystąpił błąd podczas tworzenia Pull Requestu.")
        traceback.print_exc()
        await interaction.followup.send(content="Wystąpił krytyczny błąd! Skontaktuj się z administratorem.", ephemeral=True)