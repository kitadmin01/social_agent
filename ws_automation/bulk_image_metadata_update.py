# WordPress Image Metadata Bulk Update Script
# Automates the process of updating alt text, captions, and descriptions for WordPress media library images
# Uses OpenAI to generate SEO-friendly metadata based on image context

import time
import openai
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import config
from rich import print
from typing import Dict, Optional
import json
import math

class WordPressImageMetadataUpdater:
    """
    Class to handle bulk updates of WordPress image metadata.
    Uses Playwright for browser automation and OpenAI for generating metadata content.
    """
    
    def __init__(self):
        # Initialize configuration and counters
        self.config = config
        openai.api_key = config.ai.openai_api_key
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.total_images = 0        # Total number of images found
        self.processed_count = 0     # Number of images successfully processed
        self.skipped_count = 0       # Number of images skipped

    def __enter__(self):
        """Set up Playwright browser instance with specified configuration."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, slow_mo=self.config.playwright.slow_mo)
        self.context = self.browser.new_context(viewport={'width': 1920, 'height': 1080})
        self.page = self.context.new_page()
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
        """Log into WordPress admin panel."""
        try:
            print("[bold blue]Logging into WordPress...[/bold blue]")
            self.page.goto(f"{self.config.wp.url}/wp-login.php")
            time.sleep(2)
            self.page.fill("#user_login", self.config.wp.username)
            self.page.fill("#user_pass", self.config.wp.password)
            self.page.click("#wp-submit")
            self.page.wait_for_selector("#wpadminbar")
            print("[bold green]Logged in![/bold green]")
            return True
        except Exception as e:
            print(f"[bold red]Failed to login: {str(e)}[/bold red]")
            return False

    def get_total_pages(self):
        """
        Calculate total number of pages in the media library list view.
        Each page contains 20 images.
        """
        try:
            self.page.goto(f"{self.config.wp.url}/wp-admin/upload.php?mode=list")
            self.page.wait_for_load_state('networkidle')
            
            # Extract total images count from pagination info
            total_items_text = self.page.locator('.displaying-num').first.inner_text()
            self.total_images = int(''.join(filter(str.isdigit, total_items_text)))
            total_pages = math.ceil(self.total_images / 20)  # 20 items per page
            
            print(f"[blue]Total images found: {self.total_images}[/blue]")
            print(f"[blue]Total pages: {total_pages}[/blue]")
            
            return total_pages
        except Exception as e:
            print(f"[red]Error getting total pages: {str(e)}[/red]")
            return 0

    def get_images_on_current_page(self):
        """Extract image IDs from the current page in list view."""
        try:
            print("[blue]Getting images from current page...[/blue]")
            self.page.wait_for_selector('tbody#the-list', timeout=5000)
            time.sleep(2)  # Allow table to fully load
            
            images = []
            rows = self.page.query_selector_all('tbody#the-list tr')
            print(f"[blue]Found {len(rows)} rows on current page[/blue]")
            
            for row in rows:
                try:
                    # Extract image ID from checkbox value
                    checkbox = row.query_selector('input[type="checkbox"]')
                    if not checkbox:
                        continue
                        
                    image_id = checkbox.get_attribute('value')
                    if not image_id:
                        continue
                    
                    # Get title for logging purposes
                    title_cell = row.query_selector('.column-title .title')
                    title = title_cell.inner_text() if title_cell else 'Unknown'
                    
                    print(f"[green]Found image: {title} (ID: {image_id})[/green]")
                    images.append({"id": image_id})
                    
                except Exception as e:
                    print(f"[yellow]Error processing row: {str(e)}[/yellow]")
                    continue
            
            print(f"[blue]Successfully extracted {len(images)} image IDs from current page[/blue]")
            return images
            
        except Exception as e:
            print(f"[red]Error getting images on page: {str(e)}[/red]")
            return []

    def get_image_details(self, image_id):
        """
        Get current metadata for a specific image.
        Accesses the image's edit page to retrieve title, alt text, caption, and description.
        """
        try:
            print(f"[blue]Opening image edit page for ID {image_id}...[/blue]")
            self.page.goto(f"{self.config.wp.url}/wp-admin/post.php?post={image_id}&action=edit")
            
            # Wait for page load
            self.page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            print("[blue]Waiting for image details to load...[/blue]")
            
            # Extract image details
            title = ""
            try:
                title_input = self.page.wait_for_selector('#title', timeout=5000)
                if title_input:
                    title = title_input.get_attribute('value') or f"image_{image_id}"
            except:
                title = f"image_{image_id}"
            
            # Get post title if available
            uploaded_to = ""
            try:
                post_title = self.page.locator('h1.wp-heading-inline').inner_text()
                if post_title:
                    uploaded_to = post_title
            except:
                pass
            
            # Get current metadata
            alt_text = ""
            caption = ""
            description = ""
            
            try:
                alt_input = self.page.wait_for_selector('#attachment_alt', timeout=5000)
                if alt_input:
                    alt_text = alt_input.get_attribute('value') or ""
            except:
                pass
                
            try:
                caption_input = self.page.wait_for_selector('#attachment_caption', timeout=5000)
                if caption_input:
                    caption = caption_input.get_attribute('value') or ""
            except:
                pass
                
            try:
                desc_input = self.page.wait_for_selector('#attachment_content', timeout=5000)
                if desc_input:
                    description = desc_input.get_attribute('value') or ""
            except:
                pass
            
            print(f"[green]Successfully loaded image details:[/green]")
            print(f"Title: {title}")
            print(f"Uploaded to: {uploaded_to}")
            print(f"Current alt text: {alt_text}")
            print(f"Current caption: {caption}")
            print(f"Current description: {description}")
            
            return {
                "file_name": title,
                "uploaded_to": uploaded_to,
                "current_alt_text": alt_text,
                "current_caption": caption,
                "current_description": description
            }
        except Exception as e:
            print(f"[red]Error getting image details: {str(e)}[/red]")
            return None

    def update_image_metadata(self, image_id, alt_text, caption, description):
        """Update metadata fields for a specific image."""
        try:
            print("[blue]Updating metadata fields...[/blue]")
            
            # Update Alt Text
            print("Updating alt text...")
            try:
                alt_input = self.page.wait_for_selector('#attachment_alt', timeout=5000)
                if alt_input:
                    alt_input.fill(alt_text)
                    print("[green]Alt text updated[/green]")
            except Exception as e:
                print(f"[red]Error updating alt text: {str(e)}[/red]")
            
            # Update Caption
            print("Updating caption...")
            try:
                caption_input = self.page.wait_for_selector('#attachment_caption', timeout=5000)
                if caption_input:
                    caption_input.fill(caption)
                    print("[green]Caption updated[/green]")
            except Exception as e:
                print(f"[red]Error updating caption: {str(e)}[/red]")
            
            # Update Description
            print("Updating description...")
            try:
                desc_input = self.page.wait_for_selector('#attachment_content', timeout=5000)
                if desc_input:
                    desc_input.fill(description)
                    print("[green]Description updated[/green]")
            except Exception as e:
                print(f"[red]Error updating description: {str(e)}[/red]")
            
            # Save changes
            print("Looking for Update button...")
            try:
                update_button = self.page.wait_for_selector('input.button-primary[name="save"]', timeout=5000)
                if update_button:
                    update_button.click()
                    time.sleep(2)
                    print("[green]Metadata updated successfully![/green]")
                    return True
                else:
                    print("[red]Could not find Update button[/red]")
                    return False
            
            except Exception as e:
                print(f"[red]Error clicking update button: {str(e)}[/red]")
                return False
            
        except Exception as e:
            print(f"[red]Error updating metadata: {str(e)}[/red]")
            return False

    def generate_metadata(self, file_name, uploaded_to):
        """
        Generate SEO-friendly metadata using OpenAI.
        Uses image context (filename and associated post) to generate relevant metadata.
        """
        print("\n[bold blue]Generating metadata using OpenAI[/bold blue]")
        print(f"[blue]Input parameters:[/blue]")
        print(f"File name: {file_name}")
        print(f"Uploaded to: {uploaded_to}")
        
        prompt = f"""Generate SEO-friendly metadata for an image with the following context:

Image file name: {file_name}
Used in blog post: {uploaded_to}

Please generate:
1. Alt text (brief, descriptive, SEO-friendly)
2. Caption (short, engaging description)
3. Description (detailed but concise explanation)

Format response as JSON:
{{
    "alt_text": "your alt text here",
    "caption": "your caption here",
    "description": "your description here"
}}"""

        print(f"\n[yellow]Sending prompt to OpenAI:[/yellow]")
        print(prompt)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            content = response.choices[0].message['content']
            print(f"\n[green]OpenAI Response:[/green]")
            print(content)
            
            metadata = json.loads(content)
            print("\n[blue]Parsed metadata:[/blue]")
            print(f"Alt text: {metadata['alt_text']}")
            print(f"Caption: {metadata['caption']}")
            print(f"Description: {metadata['description']}")
            
            return metadata
            
        except Exception as e:
            print(f"[red]Error generating metadata: {str(e)}[/red]")
            return None

    def process_all_images(self):
        """
        Main processing function that handles pagination and processes all images.
        Skips images that already have complete metadata.
        """
        total_pages = self.get_total_pages()
        if total_pages == 0:
            print("[red]Could not determine total pages. Exiting.[/red]")
            return
        
        current_page = 1
        while current_page <= total_pages:
            print(f"\n[bold blue]Processing Page {current_page}/{total_pages}[/bold blue]")
            print(f"[blue]Progress: {self.processed_count}/{self.total_images} images processed ({self.skipped_count} skipped)[/blue]")
            print("-" * 50)
            
            # Navigate to current page
            page_url = f"{self.config.wp.url}/wp-admin/upload.php?mode=list&paged={current_page}"
            print(f"[blue]Navigating to: {page_url}[/blue]")
            self.page.goto(page_url)
            self.page.wait_for_load_state('networkidle')
            time.sleep(3)
            
            # Process images on current page
            images = self.get_images_on_current_page()
            if not images:
                print(f"[yellow]No images found on page {current_page}, trying next page...[/yellow]")
                current_page += 1
                continue
            
            for img in images:
                print(f"\n[bold blue]Processing image ID: {img['id']}[/bold blue]")
                
                # Get and check current metadata
                details = self.get_image_details(img["id"])
                if not details:
                    print(f"[red]Failed to get details for image {img['id']}, skipping...[/red]")
                    self.skipped_count += 1
                    continue
                
                # Skip if metadata is complete
                if (details["current_alt_text"] and 
                    details["current_caption"] and 
                    details["current_description"]):
                    print("[yellow]All metadata fields already set. Skipping.[/yellow]")
                    self.skipped_count += 1
                    continue
                
                # Generate and update metadata
                metadata = self.generate_metadata(details["file_name"], details["uploaded_to"])
                if not metadata:
                    print(f"[red]Failed to generate metadata for image {img['id']}[/red]")
                    self.skipped_count += 1
                    continue
                
                if not self.update_image_metadata(img["id"], 
                                               metadata["alt_text"], 
                                               metadata["caption"], 
                                               metadata["description"]):
                    print(f"[red]Failed to update metadata for image {img['id']}[/red]")
                    self.skipped_count += 1
                else:
                    self.processed_count += 1
                
                print("-" * 50)
                time.sleep(2)
            
            current_page += 1
            time.sleep(2)
        
        # Final summary
        print(f"\n[bold green]Processing completed![/bold green]")
        print(f"Total images processed: {self.processed_count}")
        print(f"Total images skipped: {self.skipped_count}")
        print(f"Total images: {self.total_images}")

def main():
    """Main entry point for the script."""
    with WordPressImageMetadataUpdater() as updater:
        updater.login()
        updater.process_all_images()

if __name__ == "__main__":
    main()
