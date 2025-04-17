# WordPress Blog Post SEO Metadata Bulk Update Script
# Automates the process of updating Yoast SEO metadata for WordPress blog posts
# Uses OpenAI to generate SEO-optimized focus keyphrases and meta descriptions

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import config
import time
from rich import print
from typing import Dict, Optional
import openai
import json

class WordPressAutomation:
    """
    Class to handle bulk updates of WordPress blog post SEO metadata.
    Uses Playwright for browser automation and OpenAI for generating SEO content.
    """
    
    def __init__(self):
        # Initialize configuration and browser-related attributes
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        # Set up OpenAI API key
        openai.api_key = config.ai.openai_api_key

    def __enter__(self):
        """Set up Playwright browser instance with specified configuration."""
        print("\n[bold blue]Browser Configuration:[/bold blue]")
        print(f"Headless mode (from env): {self.config.playwright.headless}")
        print(f"Slow Mo (from env): {self.config.playwright.slow_mo}ms")
        
        self.playwright = sync_playwright().start()
        
        # Configure browser with specific settings
        self.browser = self.playwright.chromium.launch(
            headless=False,  # Force non-headless mode for visibility
            slow_mo=self.config.playwright.slow_mo,
            args=['--start-maximized'],  # Maximize window for better interaction
        )
        
        # Set up browser context with viewport and downloads
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},  # Large viewport for full page view
            accept_downloads=True
        )
        
        self.page = self.context.new_page()
        print("[bold green]Browser launched successfully in visible mode![/bold green]")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser resources."""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self):
        """
        Log into WordPress admin panel.
        Returns True on successful login, False otherwise.
        """
        try:
            print("[bold blue]Logging into WordPress...[/bold blue]")
            print(f"Navigating to: {self.config.wp.url}/wp-login.php")
            
            self.page.goto(f"{self.config.wp.url}/wp-login.php")
            time.sleep(2)  # Allow page to stabilize
            
            print("Filling in login credentials...")
            self.page.fill("#user_login", self.config.wp.username)
            self.page.fill("#user_pass", self.config.wp.password)
            
            print("Clicking login button...")
            self.page.click("#wp-submit")
            
            print("Waiting for dashboard to load...")
            self.page.wait_for_selector("#wpadminbar")
            print("[bold green]Successfully logged into WordPress![/bold green]")
            return True
            
        except Exception as e:
            print(f"[bold red]Failed to login: {str(e)}[/bold red]")
            print(f"Current URL: {self.page.url}")
            return False

    def navigate_to_posts(self):
        """
        Navigate to the posts listing page.
        Returns True on successful navigation, False otherwise.
        """
        try:
            print("[bold blue]Navigating to posts...[/bold blue]")
            self.page.click("text=Posts")
            self.page.wait_for_selector(".wp-list-table")
            print("[bold green]Successfully navigated to posts![/bold green]")
            return True
        except Exception as e:
            print(f"[bold red]Failed to navigate to posts: {str(e)}[/bold red]")
            return False

    def open_post_editor(self, post_id: int) -> bool:
        """
        Open the editor for a specific post.
        Handles both classic and block editor interfaces.
        Returns True if editor loads successfully, False otherwise.
        """
        try:
            print(f"[bold blue]Opening post editor for post ID: {post_id}[/bold blue]")
            
            edit_url = f"{self.config.wp.url}/wp-admin/post.php?post={post_id}&action=edit"
            print(f"[blue]Navigating directly to: {edit_url}[/blue]")
            self.page.goto(edit_url)
            time.sleep(2)

            # Check for different editor interfaces
            if self.page.locator("#post").count() > 0:
                print("[green]Successfully loaded classic editor[/green]")
                return True
            elif self.page.locator(".edit-post-header").count() > 0:
                print("[green]Successfully loaded block editor[/green]")
                return True
            else:
                print("[red]Could not detect editor interface[/red]")
                return False

        except Exception as e:
            print(f"[bold red]Failed to open post editor: {str(e)}[/bold red]")
            print("[blue]Current URL:[/blue]", self.page.url)
            return False

    def update_yoast_seo(self, post_id: int, seo_data: Dict[str, str]) -> bool:
        """
        Update Yoast SEO settings for a specific post.
        Handles focus keyphrase and meta description updates.
        Returns True if update is successful, False otherwise.
        """
        try:
            if not self.open_post_editor(post_id):
                return False

            print("[bold blue]Updating Yoast SEO settings...[/bold blue]")
            
            # Ensure all elements are loaded
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # Locate and expand Yoast SEO section
            print("[blue]Looking for Yoast SEO section...[/blue]")
            yoast_section = self.page.locator("#wpseo_meta")
            if yoast_section.count() > 0:
                # Expand if collapsed
                handle = self.page.locator("#wpseo_meta .hndle")
                if handle.count() > 0:
                    handle.click()
                    time.sleep(1)
                
                yoast_section.scroll_into_view_if_needed()
                time.sleep(2)

                # Update Focus Keyphrase
                if 'focus_keyphrase' in seo_data:
                    print("[blue]Setting focus keyphrase...[/blue]")
                    try:
                        self.page.evaluate(f'''
                            const focusInput = document.querySelector('#yoast_wpseo_focuskw');
                            if (focusInput) {{
                                focusInput.value = "{seo_data['focus_keyphrase']}";
                                focusInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            }}
                        ''')
                        print(f"[green]Focus keyphrase set to: {seo_data['focus_keyphrase']}[/green]")
                        time.sleep(1)
                    except Exception as e:
                        print(f"[red]Failed to set focus keyphrase: {str(e)}[/red]")

                # Update Meta Description
                if 'meta_description' in seo_data:
                    print("[blue]Setting meta description...[/blue]")
                    try:
                        self.page.evaluate(f'''
                            const metaDesc = document.querySelector('#yoast_wpseo_metadesc');
                            if (metaDesc) {{
                                metaDesc.value = "{seo_data['meta_description']}";
                                metaDesc.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            }}
                        ''')
                        print("[green]Meta description updated[/green]")
                        time.sleep(1)
                    except Exception as e:
                        print(f"[red]Failed to set meta description: {str(e)}[/red]")

                # Save changes
                print("[blue]Saving changes...[/blue]")
                try:
                    publish_button = self.page.locator("#publish")
                    publish_button.wait_for(state="visible", timeout=10000)
                    
                    self.page.evaluate('''
                        const publishButton = document.querySelector('#publish');
                        if (publishButton) {
                            publishButton.click();
                        }
                    ''')
                    
                    # Verify save was successful
                    try:
                        self.page.wait_for_selector(".notice-success", timeout=10000)
                        print("[bold green]Changes saved successfully![/bold green]")
                        return True
                    except PlaywrightTimeout:
                        if publish_button.count() == 0:
                            print("[bold green]Changes saved successfully![/bold green]")
                            return True
                        else:
                            print("[red]Could not confirm if changes were saved[/red]")
                            return False
                except Exception as e:
                    print(f"[red]Failed to save changes: {str(e)}[/red]")
                    return False
            else:
                print("[red]Could not find Yoast SEO section[/red]")
                return False

        except Exception as e:
            print(f"[bold red]Failed to update SEO settings: {str(e)}[/bold red]")
            print("[blue]Current URL:[/blue]", self.page.url)
            return False

    def get_seo_score(self, post_id: int) -> Optional[Dict[str, str]]:
        """
        Get the current SEO and readability scores for a post.
        Handles both classic and block editor interfaces.
        Returns a dictionary with scores and analysis or None if failed.
        """
        try:
            if not self.open_post_editor(post_id):
                return None

            print("[bold blue]Analyzing SEO scores...[/bold blue]")
            
            # Determine editor type
            is_classic = self.page.locator("#post").count() > 0
            print(f"[blue]Detected {'classic' if is_classic else 'block'} editor[/blue]")

            if is_classic:
                # Handle Classic Editor
                print("[blue]Processing Classic Editor SEO data...[/blue]")
                
                # Expand Yoast metabox if needed
                try:
                    yoast_toggle = self.page.locator("#wpseo_meta-status")
                    if yoast_toggle.count() > 0:
                        if yoast_toggle.get_attribute("aria-expanded") == "false":
                            yoast_toggle.click()
                            time.sleep(1)
                    
                    yoast_section = self.page.locator("#wpseo_meta")
                    if yoast_section.count() > 0:
                        print("[blue]Scrolling to Yoast SEO section...[/blue]")
                        yoast_section.scroll_into_view_if_needed()
                        time.sleep(1)
                    
                    # Expand all subsections
                    for section in ["focuskeyword", "metadesc", "title"]:
                        toggle = self.page.locator(f"#wpseo-meta-section-{section}")
                        if toggle.count() > 0 and toggle.get_attribute("aria-expanded") == "false":
                            toggle.click()
                            time.sleep(0.5)
                    
                except Exception as e:
                    print(f"[yellow]Warning while handling Yoast metabox: {str(e)}[/yellow]")

                # Get current values
                print("[blue]Getting focus keyphrase...[/blue]")
                focus_keyphrase = self.page.locator("#yoast_wpseo_focuskw").input_value()
                print(f"[blue]Focus keyphrase:[/blue] {focus_keyphrase or 'Not set'}")

                print("[blue]Getting meta description...[/blue]")
                meta_desc = self.page.locator("#yoast_wpseo_metadesc").input_value()
                print(f"[blue]Meta description:[/blue] {meta_desc or 'Not set'}")

                # Get SEO scores
                print("[blue]Getting SEO scores...[/blue]")
                seo_score = "Not found"
                readability_score = "Not found"
                
                score_elements = self.page.locator(".wpseo-score-icon")
                if score_elements.count() > 0:
                    seo_score = score_elements.first.get_attribute("aria-label") or "Unknown"
                if score_elements.count() > 1:
                    readability_score = score_elements.nth(1).get_attribute("aria-label") or "Unknown"

            else:
                # Handle Block Editor
                print("[blue]Processing Block Editor SEO data...[/blue]")
                
                # Open Yoast sidebar if needed
                print("[blue]Looking for Yoast SEO sidebar...[/blue]")
                yoast_button = self.page.locator('button[aria-label="Yoast SEO"]')
                if yoast_button.count() > 0:
                    if not self.page.locator('.yoast-sidebar').count() > 0:
                        yoast_button.click()
                        print("[blue]Opened Yoast SEO sidebar[/blue]")
                        time.sleep(2)
                
                # Get current values
                print("[blue]Getting focus keyphrase...[/blue]")
                focus_keyphrase = ""
                focus_input = self.page.locator('input[placeholder="Enter your focus keyphrase"]')
                if focus_input.count() > 0:
                    focus_keyphrase = focus_input.input_value()
                
                print("[blue]Getting meta description...[/blue]")
                meta_desc = ""
                meta_input = self.page.locator('textarea[placeholder="Write a meta description"]')
                if meta_input.count() > 0:
                    meta_desc = meta_input.input_value()
                
                # Get scores
                print("[blue]Getting SEO scores...[/blue]")
                seo_score = "Not found"
                readability_score = "Not found"
                
                seo_element = self.page.locator('.yoast-seo-score-icon')
                if seo_element.count() > 0:
                    seo_score = seo_element.get_attribute("aria-label") or "Unknown"
                
                readability_element = self.page.locator('.yoast-readability-score-icon')
                if readability_element.count() > 0:
                    readability_score = readability_element.get_attribute("aria-label") or "Unknown"

            # Compile results
            scores = {
                'seo_score': seo_score,
                'readability_score': readability_score,
                'focus_keyphrase': focus_keyphrase,
                'meta_description': meta_desc
            }

            print("\n[bold green]Successfully retrieved SEO analysis![/bold green]")
            print("\n[bold]Current SEO Status:[/bold]")
            for key, value in scores.items():
                print(f"[blue]{key}:[/blue] {value or 'Not set'}")

            return scores

        except Exception as e:
            print(f"[bold red]Failed to get SEO scores: {str(e)}[/bold red]")
            print("[blue]Current URL:[/blue]", self.page.url)
            return None

    def get_post_content(self, post_id: int) -> Optional[Dict[str, str]]:
        """
        Extract title and first paragraph from a blog post.
        Used for generating SEO content.
        Returns dict with title and first_paragraph or None if failed.
        """
        try:
            if not self.open_post_editor(post_id):
                return None

            print("[blue]Extracting post content...[/blue]")
            
            # Get post title
            title = ""
            title_element = self.page.locator("#title")
            if title_element.count() > 0:
                title = title_element.input_value()
                print(f"[green]Found title: {title}[/green]")

            # Get first paragraph of content
            content = ""
            content_element = self.page.locator("#content")
            if content_element.count() > 0:
                content = content_element.input_value()
                first_para = content.split('\n\n')[0].strip()
                print(f"[green]Found first paragraph: {first_para}[/green]")
            
            return {
                'title': title,
                'first_paragraph': first_para
            }
        except Exception as e:
            print(f"[red]Failed to extract post content: {str(e)}[/red]")
            return None

    def generate_seo_content(self, title: str, first_paragraph: str) -> Optional[Dict[str, str]]:
        """
        Generate SEO content using OpenAI.
        Creates focus keyphrase and meta description based on post content.
        Returns dict with generated content or None if failed.
        """
        try:
            print("[blue]Generating SEO content using OpenAI...[/blue]")
            
            prompt = f"""As an SEO expert, analyze this blog post and generate:
1. A focus keyword/keyphrase (2-3 words max)
2. A compelling meta description (under 155 characters)

Title: {title}
First Paragraph: {first_paragraph}

Format your response exactly as this JSON:
{{
    "focus_keyphrase": "your 2-3 word keyphrase",
    "meta_description": "your meta description under 155 characters"
}}"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )

            # Parse and validate response
            content = response.choices[0].message['content']
            print(f"[blue]Raw OpenAI response: {content}[/blue]")
            seo_data = json.loads(content)
            
            print("\n[bold blue]Generated SEO Content:[/bold blue]")
            print(f"[green]Focus Keyphrase: {seo_data['focus_keyphrase']}[/green]")
            print(f"[green]Meta Description: {seo_data['meta_description']}[/green]")
            
            return seo_data
            
        except Exception as e:
            print(f"[red]Failed to generate SEO content: {str(e)}[/red]")
            return None

    def get_all_post_ids_from_page(self) -> list[int]:
        """
        Get all post IDs from the current posts listing page.
        Returns list of post IDs found on the page.
        """
        try:
            print("[blue]Getting post IDs from current page...[/blue]")
            
            self.page.goto(f"{self.config.wp.url}/wp-admin/edit.php")
            time.sleep(2)
            
            post_ids = []
            rows = self.page.locator("table.wp-list-table tbody tr")
            count = rows.count()
            
            for i in range(count):
                row = rows.nth(i)
                checkbox = row.locator("input[type='checkbox']")
                if checkbox.count() > 0:
                    post_id = checkbox.get_attribute("value")
                    if post_id:
                        post_ids.append(int(post_id))
                        print(f"[green]Found post ID: {post_id}[/green]")
            
            print(f"[blue]Total posts found: {len(post_ids)}[/blue]")
            return post_ids
            
        except Exception as e:
            print(f"[red]Failed to get post IDs: {str(e)}[/red]")
            return []

    def process_all_posts(self):
        """
        Main processing function to update SEO metadata for all posts.
        Skips posts that already have complete SEO metadata.
        """
        try:
            # Get list of posts to process
            post_ids = self.get_all_post_ids_from_page()
            
            if not post_ids:
                print("[red]No posts found to process[/red]")
                return
            
            # Process each post
            for index, post_id in enumerate(post_ids, 1):
                print(f"\n[bold blue]Processing post {index} of {len(post_ids)} (ID: {post_id})[/bold blue]")
                
                # Check current SEO status
                seo_status = self.get_seo_score(post_id)
                if seo_status and seo_status.get('focus_keyphrase') and seo_status.get('meta_description'):
                    print(f"[yellow]Skipping post {post_id}: Focus keyphrase and meta description already set.[/yellow]")
                    continue
                
                # Get post content for SEO generation
                post_content = self.get_post_content(post_id)
                if not post_content:
                    print(f"[red]Failed to get content for post {post_id}, skipping...[/red]")
                    continue
                
                # Generate new SEO content
                seo_data = self.generate_seo_content(
                    post_content['title'],
                    post_content['first_paragraph']
                )
                
                if seo_data:
                    # Update Yoast SEO settings
                    print(f"[blue]Updating SEO settings for post {post_id}...[/blue]")
                    if self.update_yoast_seo(post_id, seo_data):
                        print(f"[bold green]Successfully updated post {post_id}![/bold green]")
                    else:
                        print(f"[red]Failed to update post {post_id}[/red]")
                
                time.sleep(2)  # Pause between posts
            
            print("\n[bold green]Finished processing all posts![/bold green]")
            
        except Exception as e:
            print(f"[bold red]Error processing posts: {str(e)}[/bold red]")

def main():
    """
    Main entry point for the script.
    Validates configuration and starts the automation process.
    """
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"[bold red]Configuration Error: {e}[/bold red]")
        return

    # Run automation
    with WordPressAutomation() as wp:
        if wp.login():
            time.sleep(2)
            wp.process_all_posts()

if __name__ == "__main__":
    main() 