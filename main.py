from playwright.sync_api import sync_playwright
import os
import datetime
from dotenv import load_dotenv
import time

load_dotenv()

ACCOUNT_NAME = "Marcus"
ACCOUNT_EMAIL = os.getenv("GYM_EMAIL")
ACCOUNT_PASSWORD = os.getenv("GYM_PASSWORD")

def retry(func, retries=7, description=None):
	for attempt in range(1, retries + 1):
		try:
			if description:
				print(f" Attempting: {description} (Try {attempt}/{retries})...")
			return func()
		except Exception as e:
			print(f" Warning: '{description}' failed on try {attempt}. Error: {e}")
			if attempt == retries:
				raise e
			time.sleep(1)




def run():
	user_data_dir = os.path.join(os.getcwd(), "chrome_profile")

	with sync_playwright() as p:

		context = p.chromium.launch_persistent_context(
			user_data_dir=user_data_dir,
			headless=False,
			args=[
				"--start-maximized"
				"--disable-blink-features=AutomationControlled"
			]
		)

	#page = context.new_page()
		page = context.pages[0] if context.pages else context.new_page()

		page.set_default_timeout(0)

		try:
			print("Navigating to gym schedule page...")
			page.goto("https://appbrewery.github.io/gym/")


			if page.locator("#login-button").is_visible():
				print("Login button detected. Performing login sequence...")
				retry(lambda: page.locator("#login-button").click(), description="Click Login Button")
				retry(lambda: page.wait_for_selector("#email-input", state="visible"), description="Wait for Email")
				retry(lambda: page.locator("#email-input").fill(ACCOUNT_EMAIL), description="Fill Email")
				retry(lambda: page.locator("#password-input").fill(ACCOUNT_PASSWORD), description="Fill Password")
				retry(lambda: page.locator("#submit-button").click(), description="Submit Credentials")
				retry(lambda: page.wait_for_selector("#schedule-page", state="visible"), description="Verify Schedule Page Load")



	 # if page.get_by_placeholder("Email address").is_visible():

			print("Login verified. Syncing schedule page data...")
			page.wait_for_selector("div[id^='class-card-']", state="visible")
			#page.wait_for_selector("#schedule-page", state="visible")

			all_class_cards = page.locator("div[id^='class-card-']").all()
			print(f"\n--- Scanning Schedule: Found {len(all_class_cards)} classes ---")

			new_bookings_made = 0
			waitlists_joined = 0
			already_booked_or_waitlisted = 0
			total_classes_processed = 0

			detailed_results = []

			for card in all_class_cards:
				card_id = card.get_attribute("id") or ""

				class_name = card.locator("h3").inner_text().strip()
				class_schedule = card.locator("p[id^='class-time-']").inner_text().strip()

				is_booked = card.get_attribute("data-user-booked")
				is_waitlist = card.get_attribute("data-user-waitlist")

				button_id = card_id.replace("class-card", "book-button")
				book_button = card.locator(f"#{button_id}")

				print(f"Debug card detected -> Name: '{class_name}' | schedule: '{class_schedule}'")



		# tuesday_container = page.locator('div[id^="day-group-tue"]')
		# tuesday_container.scroll_into_view_if_needed()
				if class_name == "Spin Class" and "6:00 PM" in class_schedule and ("2026-11-02" in card_id or "2026-11-05" in card_id):
					total_classes_processed += 1

					date_string = card_id.split("-")[-4:-1]
					date_obj = datetime.date(int(date_string[0]), int(date_string[1]), int(date_string[2]))
					day_name = date_obj.strftime("%A, %B")

					if is_booked == "true":
						print(f"Already booked: {class_name} Class on {class_schedule} .")
						already_booked_or_waitlisted += 1
						detailed_results.append(f" [New Waitlist] {class_name}  on {day_name} at {class_schedule} .")


					elif is_waitlist == "true":
						print(f" Already on the waitlist: {class_name} Class on {class_schedule} .")
						already_booked_or_waitlisted += 1
						detailed_results.append(f" [New Waitlist] {class_name}  on {day_name} at {class_schedule} .")


					elif book_button.locator ("text='Join Waitlist'").is_visible():
						print(f"Notice: Class is full! Joining waitlist for {class_name}...")
						card.scroll_into_view_if_needed()
						book_button.click()
						waitlists_joined += 1
						detailed_results.append(f" [New Waitlist] {class_name}  on {day_name} at {class_schedule} .")



					else:
						print(f"Notice: Spot available! Booking {class_name} on {class_schedule} ...")
						card.scroll_into_view_if_needed()
						book_button.click()
						new_bookings_made += 1
						detailed_results.append(f" [New Booking] {class_name} on {day_name} at {class_schedule} ...")


			print("\n--- BOOKING SUMMARY ---")
			print(f"Classes booked: {new_bookings_made}")
			print(f"Waitlists joined: {waitlists_joined}")
			print(f"Already booked/waitlisted: {already_booked_or_waitlisted}")
			print(f"Total classes processed: {total_classes_processed}")

			print("\n--- DETAILED CLASS LIST ---")
			for result in detailed_results:
				print(result)
			page.locator("text='My Bookings'").click()
			page.wait_for_timeout(1000)

			print("\n---RUNNING SYSTEM VERIFICATION---")

			#page.locator("div.booking-item").first.wait_for(state="visible")

			confirmed_cards = page.locator("[id^='booking-card-booking_']").all()
			waitlist_cards = page.locator("#waitlist-section div[id^='booking-card-booking_']").all()

			verified_count = 0

			for booked_card in confirmed_cards:
				name = booked_card.locator("h3").inner_text().strip()
				schedule = booked_card.locator("p:first-of-type").inner_text().strip()

				if "Spin Class" in name and("mon" in schedule.lower() or "thu" in schedule.lower()):
					verified_count += 1
					print(f" Verified: {name} on {schedule} . ")

			expected_count = new_bookings_made + waitlists_joined + already_booked_or_waitlisted

			print("\n--- VERIFICATION RESULTS ---")
			print(f"Expected: {expected_count} bookings")
			print(f"Found: {verified_count} bookings")

			if verified_count == expected_count:
				print(" SUCCESS: All bookings verified!")
			else:
				mismatch_val = expected_count - verified_count
				print(f" Mismatch: Missing {mismatch_val} bookings")

		# book_button = page.locator("#book-button-spin-2026-11-02-1800")

		# book_button.wait_for(state="visible")

		# book_button.scroll_into_view_if_needed()

		# button_text = book_button.inner_text().strip()
		except Exception as e:
			print("\n[Script Error] Something broke inside the try block:")
			import traceback
			traceback.print_exc()

		finally:
			print("\nProcess finished. The window is locked open.")
			input()
			context.close()


if __name__ == "__main__":
	run()










	print("\n Process finished. The window is locked open")
	print("Press Enter in your terminal/VS Code window whenever you are ready to close the browser.")
	input()


	#context.close()






