"""
GitHub 스킬
PyGithub 라이브러리를 직접 사용 (MCP 미사용)
"""
from github import Github
from config import GITHUB_TOKEN, GITHUB_USERNAME
from utils.logger import log


class GitHubSkill:
    def __init__(self):
        self.g = None
        if GITHUB_TOKEN:
            try:
                self.g = Github(GITHUB_TOKEN)
                log.info("GitHub 연결 완료")
            except Exception as e:
                log.error(f"GitHub 연결 실패: {e}")

    def get_briefing(self) -> str:
        """GitHub 현황 요약"""
        if not self.g:
            return "GitHub 토큰이 설정되지 않아 GitHub 정보를 가져올 수 없습니다."

        try:
            user = self.g.get_user(GITHUB_USERNAME)
            lines = []

            # 내 PR 확인
            open_prs = list(self.g.search_issues(
                f"is:pr is:open author:{GITHUB_USERNAME}"
            ))
            if open_prs:
                lines.append(f"열린 풀 리퀘스트가 {len(open_prs)}개 있습니다")

            # 리뷰 요청받은 PR
            review_requests = list(self.g.search_issues(
                f"is:pr is:open review-requested:{GITHUB_USERNAME}"
            ))
            if review_requests:
                lines.append(f"리뷰 요청이 {len(review_requests)}개 대기 중입니다")

            # 할당된 이슈
            assigned_issues = list(self.g.search_issues(
                f"is:issue is:open assignee:{GITHUB_USERNAME}"
            ))
            if assigned_issues:
                lines.append(f"담당 이슈가 {len(assigned_issues)}개 있습니다")

            # 알림
            notifications = list(user.get_notifications())
            unread = [n for n in notifications if not n.unread == False]
            if unread:
                lines.append(f"읽지 않은 GitHub 알림이 {len(unread)}개 있습니다")

            if not lines:
                return "GitHub에 현재 처리할 항목이 없습니다."

            return "GitHub 현황입니다. " + ". ".join(lines) + "."

        except Exception as e:
            log.error(f"GitHub 조회 오류: {e}")
            return "GitHub 정보를 가져오는 중 오류가 발생했습니다."

    def get_recent_commits(self, repo_name: str = None) -> str:
        """최근 커밋 현황"""
        if not self.g:
            return "GitHub 토큰이 필요합니다."

        try:
            if repo_name:
                repo = self.g.get_repo(f"{GITHUB_USERNAME}/{repo_name}")
                commits = list(repo.get_commits())[:3]
                msgs = [c.commit.message.split('\n')[0] for c in commits]
                return f"{repo_name}의 최근 커밋: " + ". ".join(msgs)
            else:
                events = list(self.g.get_user(GITHUB_USERNAME).get_events())[:5]
                push_events = [e for e in events if e.type == "PushEvent"]
                if push_events:
                    e = push_events[0]
                    repo = e.repo.name
                    commits = e.payload.get("commits", [])
                    if commits:
                        return f"최근 {repo}에 커밋: {commits[-1]['message'].split(chr(10))[0]}"
                return "최근 커밋 활동이 없습니다."
        except Exception as ex:
            return f"커밋 정보 조회 오류: {ex}"
