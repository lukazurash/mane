"""Seed content for Mane. Loaded into the database on first run; after that the admin panel owns it.

TEXTS: every word on the public site, {key: (Georgian, English)}. New keys are added on start-up without
touching keys the admin already edited.
"""

TEXTS = {
    # head
    "meta_title": ("Mane: სალონი და ბარბერშოპი საბურთალოზე, თბილისი", "Mane: hair salon and barbershop in Saburtalo, Tbilisi"),
    "meta_desc": ("ქალის სალონი და ბარბერშოპი ერთ სივრცეში. შეჭრა {from} ₾-დან. აირჩიე ოსტატი და თავისუფალი დრო და ჩაეწერე ონლაინ.",
                  "A women's salon and a barbershop under one roof. Cuts from {from} ₾. Pick a master and a free time and book online."),
    "skip": ("გადასვლა შინაარსზე", "Skip to content"),
    # nav
    "nav_services": ("მომსახურება", "Services"),
    "nav_team": ("ოსტატები", "Team"),
    "nav_visit": ("მისამართი", "Visit"),
    "nav_menu": ("მენიუ", "Menu"),
    "lang_switch": ("English", "ქართული"),
    "cta_book": ("ჩაწერა", "Book now"),
    # hero
    "hero_h1": ("სალონი და ბარბერშოპი საბურთალოზე", "Salon and barbershop in Saburtalo"),
    "hero_today": ("დღეს თავისუფალია {next}-დან", "Free today from {next}"),
    "hero_later": ("შემდეგი თავისუფალი დრო: {next}", "Next free time: {next}"),
    "hero_lead": ("ქალის სალონი და ბარბერი ერთ სივრცეში. აირჩიე ოსტატი და თავისუფალი დრო, ჩაწერა ერთ წუთს გრძელდება.",
                  "A women's salon and a barber under one roof. Pick a master and a free time: booking takes a minute."),
    # visit
    "visit_h2": ("სალონი", "The salon"),
    "visit_label": ("მისამართი", "Address"),
    "visit_area": ("იხილე რუკაზე", "See the area"),
    "visit_dirs": ("მარშრუტი", "Get directions"),
    "visit_hours": ("სამუშაო საათები", "Opening hours"),
    "visit_coffee": ("ყავა და კონსულტაცია", "Coffee and advice"),
    "visit_coffee_v": ("უფასოდ, ყველა ვიზიტზე", "Free with every visit"),
    "visit_events": ("ქორწილი და ღონისძიება", "Weddings and events"),
    "visit_events_v": ("მოგვწერე WhatsApp-ზე", "Message us on WhatsApp"),
    "ev_msg": ("გამარჯობა, Mane! მინდა ვარცხნილობა ღონისძიებისთვის.", "Hello Mane! I'd like hair styling for an event."),
    # services
    "sv_h2": ("მომსახურება და ფასები", "Services and prices"),
    "sv_line": ("ფასში შედის დაბანა და ვარცხნილობა. ხანგრძლივობა მიახლოებითია.", "Prices include a wash and styling. Times are approximate."),
    "cat_women": ("ქალი", "Women"),
    "cat_men": ("კაცი და ბარბერი", "Men and barber"),
    "price_from": ("{p} ₾-დან", "from {p} ₾"),
    "min": ("წთ", "min"),
    "sv_book": ("ჩაწერა", "Book"),
    # team
    "tm_h2": ("ოსტატები", "Our masters"),
    "tm_line": ("აირჩიე ოსტატი ან ჩაეწერე ნებისმიერ თავისუფალთან.", "Choose a master, or book whoever is free."),
    "tm_book": ("ჩაეწერე: {name}", "Book with {name}"),
    # chapters (photo-chapters)
    "ch_h2": ("როგორ გადის ვიზიტი", "How a visit goes"),
    "ch_lead": ("ყავიდან სარკემდე, დაახლოებით ერთ საათში.", "From coffee to the mirror in about an hour."),
    "ch1_t": ("დაბანა და საუბარი", "A wash and a talk"),
    "ch1_p": ("ჯერ თმას ვიბანთ და ვსაუბრობთ, რა გინდა. მოიტანე ფოტო ან ერთად ავარჩიოთ.",
              "We start with a wash and a talk about what you want. Bring a photo or choose with us."),
    "ch2_t": ("შეჭრა და ფორმა", "The cut and the shape"),
    "ch2_p": ("ოსტატი ჭრის შენი თმის ტიპის მიხედვით და ფენით აყენებს ფორმას.",
              "Your master cuts for your hair type and sets the shape with the dryer."),
    "ch3_t": ("საბოლოო შეხება", "The finish"),
    "ch3_p": ("ვასწორებთ დეტალებს და გაჩვენებთ, როგორ დააყენო სახლში.",
              "We tidy the details and show you how to style it at home."),
    # booking
    "bk_h2": ("ონლაინ ჩაწერა", "Book online"),
    "bk_line": ("აირჩიე მომსახურება, ოსტატი და დრო. ჩანს მხოლოდ თავისუფალი დრო.",
                "Pick a service, a master and a time. Only free times are shown."),
    "bk_service": ("მომსახურება", "Service"),
    "bk_master": ("ოსტატი", "Master"),
    "bk_any": ("ნებისმიერი თავისუფალი", "Any free master"),
    "bk_day": ("დღე", "Day"),
    "bk_time": ("დრო", "Time"),
    "bk_name": ("შენი სახელი", "Your name"),
    "bk_phone": ("ტელეფონი", "Phone"),
    "bk_phone_hint": ("არასავალდებულო", "Optional"),
    "bk_note": ("კომენტარი", "Note"),
    "bk_note_hint": ("არასავალდებულო, მაგ. თმის სიგრძე", "Optional, e.g. your hair length"),
    "bk_send": ("ჩაწერა", "Book"),
    "bk_reply": ("ჩაწერა ინახება და WhatsApp იხსნება, რომ გაგვიგზავნო. ადმინისტრატორი იქვე დაგიდასტურებს.",
                 "Your booking is saved and WhatsApp opens so you can send it. We confirm it there."),
    "bk_sent": ("ჩაწერა #{n} შენახულია. WhatsApp იხსნება, რომ გაგვიგზავნო.",
                "Booking #{n} is saved. WhatsApp opens so you can send it to us."),
    "bk_sending": ("იგზავნება", "Sending"),
    "bk_failed": ("ვერ გაიგზავნა, კავშირი გაწყდა. შენი ტექსტი შენახულია, სცადე თავიდან.",
                  "Not sent: the connection failed. Your words are still here, try again."),
    "bk_fix": ("გასასწორებელი ველები: {n}", "{n} fields to fix."),
    "bk_none": ("ამ დღეს თავისუფალი დრო აღარ არის. აირჩიე სხვა დღე.", "No free times left this day. Pick another day."),
    "bk_closed": ("ამ დღეს სალონი დაკეტილია. აირჩიე სხვა დღე.", "The salon is closed this day. Pick another day."),
    "bk_pick_time": ("აირჩიე დრო", "Pick a time"),
    # field errors
    "e_service": ("აირჩიე მომსახურება სიიდან.", "Pick a service from the list."),
    "e_master": ("აირჩიე ოსტატი სიიდან.", "Pick a master from the list."),
    "e_day": ("აირჩიე დღე, დღეიდან {ahead} დღის ფარგლებში.", "Pick a day within the next {ahead} days."),
    "e_closed": ("ამ დღეს სალონი დაკეტილია.", "The salon is closed that day."),
    "e_time": ("აირჩიე თავისუფალი დრო.", "Pick a free time."),
    "e_taken": ("ეს დრო ახლახან დაიკავეს. აირჩიე სხვა.", "Someone just took this time. Pick another."),
    "e_name": ("დაწერე სახელი, ვისი სახელითაც არის ჩაწერა.", "Write the name the booking is under."),
    "e_phone": ("დაწერე ტელეფონი ციფრებით, მაგ. 5xx xx xx xx.", "Write the phone as digits, like 5xx xx xx xx."),
    "e_note": ("კომენტარი 120 სიმბოლომდე უნდა იყოს.", "Keep the note under 120 characters."),
    "e_busy": ("ძალიან ბევრი მოთხოვნა. სცადე რამდენიმე წუთში.", "Too many requests. Try again in a few minutes."),
    # whatsapp message
    "m_hi": ("გამარჯობა, Mane! მინდა ჩაწერა:", "Hello Mane! I'd like to book:"),
    "m_booking": ("ჩაწერა", "Booking"),
    "m_service": ("მომსახურება", "Service"),
    "m_master": ("ოსტატი", "Master"),
    "m_when": ("დრო", "When"),
    "m_name": ("სახელი", "Name"),
    "m_phone": ("ტელეფონი", "Phone"),
    "m_note": ("კომენტარი", "Note"),
    "m_hello": ("გამარჯობა, Mane!", "Hello Mane!"),
    # close and footer
    "close_h2": ("ჩაეწერე ერთ წუთში", "Book in a minute"),
    "close_line": ("აირჩიე ოსტატი და დრო, ჩვენ WhatsApp-ზე დაგიდასტურებთ.", "Pick a master and a time, and we confirm on WhatsApp."),
    "foot_wa": ("მოგვწერე WhatsApp-ზე", "Message us on WhatsApp"),
    "foot_privacy": ("კონფიდენციალურობა", "Privacy"),
    "foot_by": ("საიტი: ლუკა", "Site by Luka"),
    "credits_line": ("ფოტოები: Unsplash", "Photographs via Unsplash"),
    "credits_h1": ("ფოტოების ავტორები", "Photograph credits"),
    "privacy_h1": ("კონფიდენციალურობა", "Privacy"),
    "privacy_body": ("ჩაწერისას ვინახავთ შენს სახელს, ტელეფონს (თუ მიუთითებ), მომსახურებას, დღეს, დროს და კომენტარს, მხოლოდ ვიზიტის მოსაწყობად. მონაცემებს არავის ვუზიარებთ. წაშლა რომ გინდოდეს, მოგვწერე WhatsApp-ზე.",
                     "When you book we keep your name, your phone if you give it, the service, the day, the time and your note, only to arrange the visit. We share them with no one. To have them deleted, message us on WhatsApp."),
    "nf_h1": ("გვერდი ვერ მოიძებნა", "Page not found"),
    "nf_line": ("ეს ბმული აღარ მუშაობს. მომსახურება და ჩაწერა მთავარ გვერდზეა.", "This link no longer works. Services and booking are on the home page."),
    "back_home": ("მთავარი გვერდი", "Home page"),
    # photo alt text
    "alt_hero": ("სალონის დარბაზი: სავარძლები, მრგვალი სარკეები და აგურის კედელი", "The salon floor: chairs, round mirrors and a brick wall"),
    "alt_visit": ("შავი სავარძლები მრგვალი სარკეების წინ", "Black chairs in front of round mirrors"),
    "alt_ch1": ("ოსტატი კლიენტს თმას ბანს ნიჟარასთან", "A stylist washing a client's hair at the basin"),
    "alt_ch2": ("ოსტატი ფენით და სავარცხლით აყენებს თმას", "A stylist blow-drying a client's hair with a round brush"),
    "alt_ch3": ("ოსტატი კლიენტს ხსნის პელერინას, კლიენტი იღიმება", "A stylist lifts the cape off a smiling client"),
    "alt_women": ("ოსტატი უხვევს გრძელ თმას", "A stylist curling long hair"),
    "alt_men": ("ბარბერი ჭრის კლიენტის წვერს", "A barber trimming a client's beard"),
}

SETTINGS = {
    "shop_name": "Mane",
    "whatsapp": "995000000000",  # the salon's WhatsApp number, international format without +
    "street": "",                # empty: the site names the district only and links "See the area"
    "district_ka": "საბურთალო",
    "district_en": "Saburtalo",
    "city_ka": "თბილისი",
    "city_en": "Tbilisi",
    # shown on the site: one row per line: days for system.js (mon-sun, sat,sun ...) | Georgian label | English label | time
    "hours": "mon-sun|ყოველდღე|Every day|10:00–21:00",
    "hours_assumed": "1",        # 1 until the owner confirms the hours: no "open now" line is shown
    # used by the booking: first and last time, slot step, days closed, notice for today, how far ahead
    "open": "10:00",
    "close": "21:00",
    "step": "30",
    "days_off": "",              # comma list of mon,tue,wed,thu,fri,sat,sun
    "lead": "30",                # minutes of notice for a booking today
    "days_ahead": "30",
    "site_by_url": "https://lukazurash.github.io",
}

# (category, Georgian name, English name, Georgian line, English line, price, "from" price, minutes)
SERVICES = [
    ("women", "ქალის შეჭრა", "Women's haircut", "დაბანა, შეჭრა და ვარცხნილობა", "Wash, cut and blow-dry", 45, 0, 60),
    ("women", "ვარცხნილობა", "Blow-dry and styling", "დაბანა და ფენით დაყენება", "Wash and blow-dry", 35, 0, 45),
    ("women", "საღამოს ვარცხნილობა", "Evening updo", "ღონისძიებისთვის ან ქორწილისთვის", "For events and weddings", 70, 0, 90),
    ("women", "თმის შეღებვა", "Colouring", "ერთ ტონში, ფასი თმის სიგრძეზეა დამოკიდებული", "Single tone, priced by length", 120, 1, 120),
    ("women", "ბალაიაჟი და მელირება", "Balayage and highlights", "ბუნებრივი გადასვლა და სიკაშკაშე", "A soft, natural-looking blend", 220, 1, 180),
    ("women", "კერატინი", "Keratin treatment", "გლუვი და ბზინვარე თმა 3–4 თვე", "Smooth, glossy hair for 3 to 4 months", 150, 1, 150),
    ("women", "თმის მოვლა", "Hair treatment", "აღმდგენი ნიღაბი და მასაჟი", "Repair mask and scalp massage", 50, 0, 40),
    ("men", "კაცის შეჭრა", "Men's haircut", "მაკრატლით ან მანქანით, დაბანით", "Scissors or clippers, with a wash", 30, 0, 40),
    ("men", "ფეიდი", "Skin fade", "სუფთა, მკვეთრი გადასვლა", "A clean, sharp fade", 35, 0, 45),
    ("men", "წვერის მოწესრიგება", "Beard trim", "ფორმა, კონტური და ზეთი", "Shape, line-up and oil", 20, 0, 20),
    ("men", "შეჭრა და წვერი", "Haircut and beard", "ყველაზე პოპულარული", "Our most popular", 45, 0, 60),
    ("men", "კლასიკური პარსვა", "Hot towel shave", "ცხელი პირსახოცით და სამართებლით", "Hot towel and straight razor", 30, 0, 30),
    ("men", "ბავშვის შეჭრა", "Kids' haircut", "12 წლამდე", "Up to age 12", 20, 0, 30),
]

# (category, Georgian name, English name, Georgian role, English role, Georgian line, English line, colour)
MASTERS = [
    ("women", "ნინო", "Nino", "კოლორისტი", "Colourist", "შეღებვა, ბალაიაჟი, რთული ტონები", "Colour, balayage, tricky tones", "#9a7448"),
    ("women", "ანა", "Ana", "სტილისტი", "Stylist", "შეჭრა და საღამოს ვარცხნილობები", "Cuts and evening updos", "#7d6079"),
    ("men", "გიორგი", "Giorgi", "ბარბერი", "Barber", "ფეიდი და კლასიკური შეჭრა", "Fades and classic cuts", "#4c5b52"),
    ("men", "ლევანი", "Levani", "ბარბერი", "Barber", "წვერი და ცხელი პირსახოცით პარსვა", "Beards and hot towel shaves", "#5a4a3f"),
]

# site photo slots: slot -> (source file, make a 4:5 phone crop, focus x, focus y)
PHOTOS = {
    "hero": ("interior2.jpg", True, 0.5, 0.55),
    "visit": ("chairs.jpg", False, 0.4, 0.5),
    "women": ("curler.jpg", False, 0.5, 0.4),
    "men": ("razor.jpg", False, 0.5, 0.4),
    "ch1": ("woman1.jpg", False, 0.5, 0.5),
    "ch2": ("blowdry.jpg", False, 0.5, 0.5),
    "ch3": ("cape.jpg", False, 0.6, 0.4),
}

# credits for the stand-in photographs, by source file (shown on /credits while the photograph is on the site)
CREDITS = {}
UNSPLASH = "Unsplash, Unsplash License|https://unsplash.com/license"
