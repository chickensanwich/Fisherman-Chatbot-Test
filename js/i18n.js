// ==================== UI TRANSLATIONS ====================
// Controls the language of on-screen UI text (labels, buttons, alerts, etc).
// This is independent of the chatbot's own message-language detection
// (server.py detect_language), which keeps auto-detecting per message
// regardless of what the user picks here.

const UI_LANG_STORAGE_KEY = 'uiLang';
const DEFAULT_UI_LANG     = 'bn';

const translations = {
    bn: {
        appTitle: "মৎস্যজীবী চ্যাটবট",
        appLogoAlt: "মৎস্যজীবী চ্যাটবট লোগো",

        "login.heading": "প্রবেশ করুন",
        "login.idLabel": "মৎস্যজীবী আইডি",
        "login.idPlaceholder": "আপনার মৎস্যজীবী আইডি লিখুন",
        "login.passwordLabel": "পাসওয়ার্ড",
        "login.passwordPlaceholder": "আপনার পাসওয়ার্ড লিখুন",
        "login.submit": "প্রবেশ করুন",
        "login.noAccount": "অ্যাকাউন্ট নেই?",
        "login.signupLink": "নতুন অ্যাকাউন্ট তৈরি করুন",
        "login.missingFields": "অনুগ্রহ করে মৎস্যজীবী আইডি এবং পাসওয়ার্ড লিখুন",
        "login.invalidCredentials": "ভুল তথ্য দেওয়া হয়েছে",
        "login.failedPrefix": "প্রবেশ করতে ব্যর্থ হয়েছে: ",
        "login.welcomeBack": "আপনাকে পুনরায় স্বাগতম!",

        "signup.heading": "নতুন অ্যাকাউন্ট তৈরি করুন",
        "signup.nameLabel": "নাম",
        "signup.namePlaceholder": "আপনার নাম লিখুন",
        "signup.countryLabel": "দেশ",
        "signup.countryDefault": "দেশ নির্বাচন করুন",
        "signup.locationLabel": "অবস্থান",
        "signup.locationPlaceholder": "আপনার বর্তমান অবস্থান লিখুন",
        "signup.confirmPasswordLabel": "পাসওয়ার্ড নিশ্চিত করুন",
        "signup.confirmPasswordPlaceholder": "পাসওয়ার্ড পুনরায় লিখুন",
        "signup.submit": "নিবন্ধন করুন",
        "signup.haveAccount": "ইতোমধ্যে অ্যাকাউন্ট আছে?",
        "signup.loginLink": "প্রবেশ করুন",
        "signup.selectCountry": "অনুগ্রহ করে একটি দেশ নির্বাচন করুন",
        "signup.passwordTooShort": "পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে",
        "signup.passwordMismatch": "পাসওয়ার্ড মিলছে না!",
        "signup.idInvalidChars": "মৎস্যজীবী আইডিতে শুধুমাত্র ইংরেজি অক্ষর এবং সংখ্যা থাকতে হবে",
        "signup.failedGeneric": "নিবন্ধন ব্যর্থ হয়েছে",
        "signup.success": "অ্যাকাউন্ট জমা দেওয়া হয়েছে! প্রবেশ করার আগে অনুগ্রহ করে অ্যাডমিনের অনুমোদনের জন্য অপেক্ষা করুন।",
        "signup.failedPrefix": "নিবন্ধন করতে ব্যর্থ হয়েছে: ",

        "country.australia": "অস্ট্রেলিয়া",
        "country.malaysia": "মালয়েশিয়া",
        "country.india": "ভারত",
        "country.bangladesh": "বাংলাদেশ",
        "country.usa": "যুক্তরাষ্ট্র",
        "country.uk": "যুক্তরাজ্য",

        "sidebarToggle.title": "সাইডবার টগল করুন",
        "sidebar.newChat": "নতুন চ্যাট",
        "sidebar.searchPlaceholder": "চ্যাট খুঁজুন",
        "sidebar.profileTitle": "প্রোফাইল অপশন",
        "sidebar.defaultUserName": "ব্যবহারকারীর নাম",
        "sidebar.logoutTitle": "লগআউট",
        "sidebar.themeToggle": "থিম পরিবর্তন করুন",
        "sidebar.exportChat": "চ্যাট এক্সপোর্ট করুন",
        "sidebar.contributeTitle": "নলেজ গ্রাফে অবদান রাখুন",
        "sidebar.contributeLabel": "নতুন তথ্য যোগ করুন",
        "user.defaultName": "মৎস্যজীবী",

        "chat.welcomeTitle": "মৎস্যজীবী চ্যাটবটে স্বাগতম",
        "chat.welcomeSubtitle": "আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
        "chat.welcomeReturnSubtitle": "কথোপকথন শুরু করতে আপনার প্রথম মেসেজটি পাঠান...",
        "chat.inputPlaceholder": "আপনার মেসেজ এখানে লিখুন...",
        "chat.voiceInputTitle": "ভয়েস ইনপুট",
        "chat.sendTitle": "পাঠান",
        "chat.disclaimer": "এই চ্যাটবটটি প্রাপ্ত তথ্যের ভিত্তিতে নির্দেশনা প্রদান করে এবং এটি সর্বদা নির্ভুল বা সর্বশেষ তথ্য নাও হতে পারে। শুধুমাত্র এই তথ্যের উপর নির্ভর করবেন না। গুরুত্বপূর্ণ সিদ্ধান্তের জন্য প্রয়োজনে স্থানীয় কর্তৃপক্ষ বা অভিজ্ঞ জেলেদের পরামর্শ নিন।",
        "chat.notFound": "চ্যাটটি পাওয়া যায়নি।",
        "chat.deleteFailed": "চ্যাটটি মুছে ফেলা যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন।",
        "chat.createFailed": "নতুন চ্যাট তৈরি করা যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন।",
        "chat.notLoggedIn": "অনুগ্রহ করে প্রথমে প্রবেশ (Login) করুন এবং একটি নতুন চ্যাট তৈরি করুন।",
        "chat.serverUnreachable": "চ্যাটবট সার্ভারের সাথে যোগাযোগ করা যাচ্ছে না। অনুগ্রহ করে নিশ্চিত করুন যে ব্যাকএন্ড চালু আছে।",

        "feedback.heading": "এই উত্তরে কী সমস্যা ছিল?",
        "feedback.incorrect": "ভুল তথ্য",
        "feedback.harmful": "ক্ষতিকারক বা অনিরাপদ বিষয়বস্তু",
        "feedback.notHelpful": "উপকারী নয়",
        "feedback.other": "অন্যান্য",
        "feedback.commentPlaceholder": "অতিরিক্ত মন্তব্য (ঐচ্ছিক)",
        "feedback.thanks": "আপনার মূল্যবান মতামতের জন্য ধন্যবাদ!",

        "common.cancel": "বাতিল করুন",
        "common.submit": "জমা দিন",
        "common.close": "বন্ধ করুন",

        "menu.rename": "নাম পরিবর্তন",
        "menu.pin": "পিন করুন",
        "menu.unpin": "আনপিন করুন",
        "menu.share": "শেয়ার করুন",
        "menu.delete": "মুছে ফেলুন",
        "menu.confirmDelete": "আপনি কি এই চ্যাটটি স্থায়ীভাবে মুছে ফেলতে চান?",
        "pin.failed": "পিন স্ট্যাটাস পরিবর্তন করা সম্ভব হয়নি।",
        "rename.prompt": "এই চ্যাটের জন্য একটি নতুন নাম লিখুন:",
        "rename.failed": "চ্যাটের নাম পরিবর্তন করা যায়নি।",

        "share.defaultTitle": "মৎস্যজীবী চ্যাটবট কথোপকথন",
        "share.you": "আপনি",
        "share.sharedFooter": "মৎস্যজীবী চ্যাটবট থেকে শেয়ার করা হয়েছে",
        "share.modalTitle": "চ্যাট শেয়ার করুন",
        "share.copyText": "লেখা কপি করুন",
        "share.copiedSuccess": "ক্লিপবোর্ডে কপি করা হয়েছে!",
        "share.copyFailed": "কপি করা যায়নি। অনুগ্রহ করে নিজে সিলেক্ট করে কপি করুন।",
        "share.shareFailed": "চ্যাটটি শেয়ার করা সম্ভব হয়নি।",

        "readAloud.listen": "শুনুন",
        "readAloud.stop": "পড়া বন্ধ করুন",

        "voice.closeTitle": "বাতিল করুন",
        "voice.initialPrompt": "এখন কথা বলুন...",
        "voice.stopRecordingTitle": "রেকর্ডিং বন্ধ করুন",
        "voice.send": "পাঠান",
        "voice.startingMic": "মাইক্রোফোন চালু হচ্ছে...",
        "voice.transcribingWait": "প্রতিলিপি (Transcribe) করা হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন",
        "voice.listening": "শুনছি...",
        "voice.micDenied": "মাইক্রোফোন ব্যবহারের অনুমতি দেওয়া হয়নি।",
        "voice.unclear": "আপনার কথা পরিষ্কারভাবে শোনা যায়নি। অনুগ্রহ করে আবার রেকর্ড করুন।",
        "voice.transcribeError": "প্রতিলিপি করার সময় সার্ভারে ত্রুটি ঘটেছে।",
        "voice.transcribing": "প্রতিলিপি করা হচ্ছে...",
        "voice.stepUpload": "অডিও আপলোড করা হচ্ছে...",
        "voice.stepProcess": "ভয়েস প্রসেস করা হচ্ছে...",
        "voice.stepDetect": "শব্দ সনাক্ত করা হচ্ছে...",
        "voice.stepAlmost": "প্রায় শেষ...",
        "voice.stepFinalize": "চূড়ান্ত করা হচ্ছে...",
        "voice.done": "সম্পন্ন হয়েছে!",

        "contribute.title": "তথ্যভাণ্ডারে নতুন তথ্য যোগ করুন",
        "contribute.description": "একজন মৎস্যজীবী হিসেবে আপনার জানা একটি তথ্য শেয়ার করুন। নিচে টাইপ করুন বা মাইক ব্যবহার করুন। আপনার দেওয়া তথ্য যোগ করার আগে যাচাই করা হবে।",
        "contribute.tabText": "টাইপ করুন",
        "contribute.tabVoice": "কথা বলুন",
        "contribute.subjectLabel": "বিষয় (Subject)",
        "contribute.subjectPlaceholder": "যেমন: Hilsa, Shrimp, Cast Net",
        "contribute.relationLabel": "সম্পর্ক (Relationship)",
        "contribute.relationPlaceholder": "যেমন: FOUND_IN, NEEDS, BEST_IN",
        "contribute.objectLabel": "অবজেক্ট (Object)",
        "contribute.objectPlaceholder": "যেমন: Padma River, Winter, Monsoon, June",
        "contribute.contextLabel": "অতিরিক্ত তথ্য",
        "contribute.optional": "(ঐচ্ছিক)",
        "contribute.contextPlaceholder": "যেমন: বর্ষাকালে পদ্মা নদীতে ইলিশ সবচেয়ে বেশি পাওয়া যায়।",
        "contribute.voicePanelDesc": "তথ্যটি বর্ণনা করে একটি পূর্ণ বাক্য বলুন। আমরা এটি প্রতিলিপি (transcribe) করে আপনার জন্য অতিরিক্ত তথ্যের ক্ষেত্রটি পূরণ করব।",
        "contribute.pressMicToStart": "শুরু করতে মাইক চাপুন...",
        "contribute.useTranscript": "এই লেখাটি ব্যবহার করুন",
        "contribute.submit": "জমা দিন",
        "contribute.missingFields": "অনুগ্রহ করে বিষয় (Subject), সম্পর্ক (Relationship) এবং অবজেক্ট (Object) পূরণ করুন।",
        "contribute.submitting": "জমা দেওয়া হচ্ছে...",
        "contribute.successMsg": "পর্যালোচনার জন্য জমা দেওয়া হয়েছে!",
        "contribute.failedGeneric": "জমা দেওয়া সম্ভব হয়নি"
    },
    en: {
        appTitle: "Fisherman Chatbot",
        appLogoAlt: "Fisherman Chatbot logo",

        "login.heading": "Log In",
        "login.idLabel": "Fisherman ID",
        "login.idPlaceholder": "Enter your Fisherman ID",
        "login.passwordLabel": "Password",
        "login.passwordPlaceholder": "Enter your password",
        "login.submit": "Log In",
        "login.noAccount": "Don't have an account?",
        "login.signupLink": "Create a new account",
        "login.missingFields": "Please enter your Fisherman ID and password",
        "login.invalidCredentials": "Invalid credentials",
        "login.failedPrefix": "Login failed: ",
        "login.welcomeBack": "Welcome back!",

        "signup.heading": "Create a New Account",
        "signup.nameLabel": "Name",
        "signup.namePlaceholder": "Enter your name",
        "signup.countryLabel": "Country",
        "signup.countryDefault": "Select a country",
        "signup.locationLabel": "Location",
        "signup.locationPlaceholder": "Enter your current location",
        "signup.confirmPasswordLabel": "Confirm Password",
        "signup.confirmPasswordPlaceholder": "Re-enter your password",
        "signup.submit": "Sign Up",
        "signup.haveAccount": "Already have an account?",
        "signup.loginLink": "Log In",
        "signup.selectCountry": "Please select a country",
        "signup.passwordTooShort": "Password must be at least 8 characters",
        "signup.passwordMismatch": "Passwords do not match!",
        "signup.idInvalidChars": "Fisherman ID must contain only English letters and numbers",
        "signup.failedGeneric": "Sign up failed",
        "signup.success": "Account submitted! Please wait for admin approval before logging in.",
        "signup.failedPrefix": "Sign up failed: ",

        "country.australia": "Australia",
        "country.malaysia": "Malaysia",
        "country.india": "India",
        "country.bangladesh": "Bangladesh",
        "country.usa": "USA",
        "country.uk": "UK",

        "sidebarToggle.title": "Toggle sidebar",
        "sidebar.newChat": "New Chat",
        "sidebar.searchPlaceholder": "Search chats",
        "sidebar.profileTitle": "Profile options",
        "sidebar.defaultUserName": "User Name",
        "sidebar.logoutTitle": "Log out",
        "sidebar.themeToggle": "Change theme",
        "sidebar.exportChat": "Export chat",
        "sidebar.contributeTitle": "Contribute to knowledge graph",
        "sidebar.contributeLabel": "Add new information",
        "user.defaultName": "Fisherman",

        "chat.welcomeTitle": "Welcome to the Fisherman Chatbot",
        "chat.welcomeSubtitle": "How can I help you today?",
        "chat.welcomeReturnSubtitle": "Send your first message to start the conversation...",
        "chat.inputPlaceholder": "Type your message here...",
        "chat.voiceInputTitle": "Voice input",
        "chat.sendTitle": "Send",
        "chat.disclaimer": "This chatbot provides guidance based on the information it has, which may not always be accurate or up to date. Do not rely on this information alone. For important decisions, consult local authorities or experienced fishermen when needed.",
        "chat.notFound": "Chat not found.",
        "chat.deleteFailed": "Could not delete the chat. Please try again.",
        "chat.createFailed": "Could not create a new chat. Please try again.",
        "chat.notLoggedIn": "Please log in first and create a new chat.",
        "chat.serverUnreachable": "Could not reach the chatbot server. Please make sure the backend is running.",

        "feedback.heading": "What was wrong with this response?",
        "feedback.incorrect": "Incorrect information",
        "feedback.harmful": "Harmful or unsafe content",
        "feedback.notHelpful": "Not helpful",
        "feedback.other": "Other",
        "feedback.commentPlaceholder": "Additional comments (optional)",
        "feedback.thanks": "Thank you for your valuable feedback!",

        "common.cancel": "Cancel",
        "common.submit": "Submit",
        "common.close": "Close",

        "menu.rename": "Rename",
        "menu.pin": "Pin",
        "menu.unpin": "Unpin",
        "menu.share": "Share",
        "menu.delete": "Delete",
        "menu.confirmDelete": "Are you sure you want to permanently delete this chat?",
        "pin.failed": "Could not change pin status.",
        "rename.prompt": "Enter a new name for this chat:",
        "rename.failed": "Could not rename the chat.",

        "share.defaultTitle": "Fisherman Chatbot conversation",
        "share.you": "You",
        "share.sharedFooter": "Shared from Fisherman Chatbot",
        "share.modalTitle": "Share Chat",
        "share.copyText": "Copy text",
        "share.copiedSuccess": "Copied to clipboard!",
        "share.copyFailed": "Could not copy. Please select and copy the text manually.",
        "share.shareFailed": "Could not share the chat.",

        "readAloud.listen": "Listen",
        "readAloud.stop": "Stop reading",

        "voice.closeTitle": "Cancel",
        "voice.initialPrompt": "Speak now...",
        "voice.stopRecordingTitle": "Stop recording",
        "voice.send": "Send",
        "voice.startingMic": "Starting microphone...",
        "voice.transcribingWait": "Transcribing... please wait",
        "voice.listening": "Listening...",
        "voice.micDenied": "Microphone permission was denied.",
        "voice.unclear": "Your speech wasn't clear. Please record again.",
        "voice.transcribeError": "A server error occurred during transcription.",
        "voice.transcribing": "Transcribing...",
        "voice.stepUpload": "Uploading audio...",
        "voice.stepProcess": "Processing voice...",
        "voice.stepDetect": "Detecting speech...",
        "voice.stepAlmost": "Almost done...",
        "voice.stepFinalize": "Finalizing...",
        "voice.done": "Done!",

        "contribute.title": "Add New Information to the Knowledge Base",
        "contribute.description": "Share something you know as a fisherman. Type below or use the mic. Your contribution will be reviewed before it's added.",
        "contribute.tabText": "Type",
        "contribute.tabVoice": "Speak",
        "contribute.subjectLabel": "Subject",
        "contribute.subjectPlaceholder": "e.g., Hilsa, Shrimp, Cast Net",
        "contribute.relationLabel": "Relationship",
        "contribute.relationPlaceholder": "e.g., FOUND_IN, NEEDS, BEST_IN",
        "contribute.objectLabel": "Object",
        "contribute.objectPlaceholder": "e.g., Padma River, Winter, Monsoon, June",
        "contribute.contextLabel": "Additional information",
        "contribute.optional": "(optional)",
        "contribute.contextPlaceholder": "e.g., Hilsa is most abundant in the Padma River during the monsoon season.",
        "contribute.voicePanelDesc": "Say a full sentence describing the information. We'll transcribe it and fill in the additional information field for you.",
        "contribute.pressMicToStart": "Press the mic to start...",
        "contribute.useTranscript": "Use this text",
        "contribute.submit": "Submit",
        "contribute.missingFields": "Please fill in Subject, Relationship, and Object.",
        "contribute.submitting": "Submitting...",
        "contribute.successMsg": "Submitted for review!",
        "contribute.failedGeneric": "Submission failed"
    },
    id: {
        appTitle: "Chatbot Nelayan",
        appLogoAlt: "Logo Chatbot Nelayan",

        "login.heading": "Masuk",
        "login.idLabel": "ID Nelayan",
        "login.idPlaceholder": "Masukkan ID Nelayan Anda",
        "login.passwordLabel": "Kata Sandi",
        "login.passwordPlaceholder": "Masukkan kata sandi Anda",
        "login.submit": "Masuk",
        "login.noAccount": "Belum punya akun?",
        "login.signupLink": "Buat akun baru",
        "login.missingFields": "Mohon masukkan ID Nelayan dan kata sandi Anda",
        "login.invalidCredentials": "Data yang dimasukkan salah",
        "login.failedPrefix": "Gagal masuk: ",
        "login.welcomeBack": "Selamat datang kembali!",

        "signup.heading": "Buat Akun Baru",
        "signup.nameLabel": "Nama",
        "signup.namePlaceholder": "Masukkan nama Anda",
        "signup.countryLabel": "Negara",
        "signup.countryDefault": "Pilih negara",
        "signup.locationLabel": "Lokasi",
        "signup.locationPlaceholder": "Masukkan lokasi Anda saat ini",
        "signup.confirmPasswordLabel": "Konfirmasi Kata Sandi",
        "signup.confirmPasswordPlaceholder": "Masukkan ulang kata sandi Anda",
        "signup.submit": "Daftar",
        "signup.haveAccount": "Sudah punya akun?",
        "signup.loginLink": "Masuk",
        "signup.selectCountry": "Mohon pilih sebuah negara",
        "signup.passwordTooShort": "Kata sandi harus terdiri dari minimal 8 karakter",
        "signup.passwordMismatch": "Kata sandi tidak cocok!",
        "signup.idInvalidChars": "ID Nelayan hanya boleh berisi huruf Inggris dan angka",
        "signup.failedGeneric": "Pendaftaran gagal",
        "signup.success": "Akun berhasil dikirim! Mohon tunggu persetujuan admin sebelum masuk.",
        "signup.failedPrefix": "Gagal mendaftar: ",

        "country.australia": "Australia",
        "country.malaysia": "Malaysia",
        "country.india": "India",
        "country.bangladesh": "Bangladesh",
        "country.usa": "Amerika Serikat",
        "country.uk": "Inggris",

        "sidebarToggle.title": "Alihkan bilah sisi",
        "sidebar.newChat": "Obrolan Baru",
        "sidebar.searchPlaceholder": "Cari obrolan",
        "sidebar.profileTitle": "Opsi profil",
        "sidebar.defaultUserName": "Nama Pengguna",
        "sidebar.logoutTitle": "Keluar",
        "sidebar.themeToggle": "Ubah tema",
        "sidebar.exportChat": "Ekspor obrolan",
        "sidebar.contributeTitle": "Berkontribusi ke graf pengetahuan",
        "sidebar.contributeLabel": "Tambahkan informasi baru",
        "user.defaultName": "Nelayan",

        "chat.welcomeTitle": "Selamat Datang di Chatbot Nelayan",
        "chat.welcomeSubtitle": "Bagaimana saya bisa membantu Anda hari ini?",
        "chat.welcomeReturnSubtitle": "Kirim pesan pertama Anda untuk memulai percakapan...",
        "chat.inputPlaceholder": "Ketik pesan Anda di sini...",
        "chat.voiceInputTitle": "Masukan suara",
        "chat.sendTitle": "Kirim",
        "chat.disclaimer": "Chatbot ini memberikan panduan berdasarkan informasi yang dimilikinya, yang mungkin tidak selalu akurat atau terkini. Jangan hanya mengandalkan informasi ini. Untuk keputusan penting, konsultasikan dengan otoritas setempat atau nelayan berpengalaman jika diperlukan.",
        "chat.notFound": "Obrolan tidak ditemukan.",
        "chat.deleteFailed": "Obrolan tidak dapat dihapus. Silakan coba lagi.",
        "chat.createFailed": "Tidak dapat membuat obrolan baru. Silakan coba lagi.",
        "chat.notLoggedIn": "Mohon masuk terlebih dahulu dan buat obrolan baru.",
        "chat.serverUnreachable": "Tidak dapat terhubung ke server chatbot. Mohon pastikan backend berjalan.",

        "feedback.heading": "Apa yang salah dengan jawaban ini?",
        "feedback.incorrect": "Informasi tidak benar",
        "feedback.harmful": "Konten berbahaya atau tidak aman",
        "feedback.notHelpful": "Tidak membantu",
        "feedback.other": "Lainnya",
        "feedback.commentPlaceholder": "Komentar tambahan (opsional)",
        "feedback.thanks": "Terima kasih atas masukan berharga Anda!",

        "common.cancel": "Batal",
        "common.submit": "Kirim",
        "common.close": "Tutup",

        "menu.rename": "Ubah nama",
        "menu.pin": "Sematkan",
        "menu.unpin": "Lepas sematan",
        "menu.share": "Bagikan",
        "menu.delete": "Hapus",
        "menu.confirmDelete": "Apakah Anda yakin ingin menghapus obrolan ini secara permanen?",
        "pin.failed": "Tidak dapat mengubah status sematan.",
        "rename.prompt": "Masukkan nama baru untuk obrolan ini:",
        "rename.failed": "Tidak dapat mengubah nama obrolan.",

        "share.defaultTitle": "Percakapan Chatbot Nelayan",
        "share.you": "Anda",
        "share.sharedFooter": "Dibagikan dari Chatbot Nelayan",
        "share.modalTitle": "Bagikan Obrolan",
        "share.copyText": "Salin teks",
        "share.copiedSuccess": "Disalin ke clipboard!",
        "share.copyFailed": "Tidak dapat menyalin. Silakan pilih dan salin teks secara manual.",
        "share.shareFailed": "Tidak dapat membagikan obrolan.",

        "readAloud.listen": "Dengarkan",
        "readAloud.stop": "Berhenti membaca",

        "voice.closeTitle": "Batal",
        "voice.initialPrompt": "Silakan bicara sekarang...",
        "voice.stopRecordingTitle": "Hentikan perekaman",
        "voice.send": "Kirim",
        "voice.startingMic": "Memulai mikrofon...",
        "voice.transcribingWait": "Mentranskripsikan... mohon tunggu",
        "voice.listening": "Mendengarkan...",
        "voice.micDenied": "Izin mikrofon ditolak.",
        "voice.unclear": "Ucapan Anda kurang jelas. Silakan rekam ulang.",
        "voice.transcribeError": "Terjadi kesalahan server saat transkripsi.",
        "voice.transcribing": "Mentranskripsikan...",
        "voice.stepUpload": "Mengunggah audio...",
        "voice.stepProcess": "Memproses suara...",
        "voice.stepDetect": "Mendeteksi ucapan...",
        "voice.stepAlmost": "Hampir selesai...",
        "voice.stepFinalize": "Menyelesaikan...",
        "voice.done": "Selesai!",

        "contribute.title": "Tambahkan Informasi Baru ke Basis Pengetahuan",
        "contribute.description": "Bagikan sesuatu yang Anda ketahui sebagai nelayan. Ketik di bawah atau gunakan mikrofon. Kontribusi Anda akan ditinjau sebelum ditambahkan.",
        "contribute.tabText": "Ketik",
        "contribute.tabVoice": "Bicara",
        "contribute.subjectLabel": "Subjek",
        "contribute.subjectPlaceholder": "misalnya: Hilsa, Udang, Jaring Lempar",
        "contribute.relationLabel": "Hubungan",
        "contribute.relationPlaceholder": "misalnya: FOUND_IN, NEEDS, BEST_IN",
        "contribute.objectLabel": "Objek",
        "contribute.objectPlaceholder": "misalnya: Sungai Padma, Musim Dingin, Musim Hujan, Juni",
        "contribute.contextLabel": "Informasi tambahan",
        "contribute.optional": "(opsional)",
        "contribute.contextPlaceholder": "misalnya: Ikan Hilsa paling banyak ditemukan di Sungai Padma pada musim hujan.",
        "contribute.voicePanelDesc": "Ucapkan satu kalimat lengkap yang menjelaskan informasinya. Kami akan mentranskripsikannya dan mengisi kolom informasi tambahan untuk Anda.",
        "contribute.pressMicToStart": "Tekan mikrofon untuk mulai...",
        "contribute.useTranscript": "Gunakan teks ini",
        "contribute.submit": "Kirim",
        "contribute.missingFields": "Mohon isi Subjek, Hubungan, dan Objek.",
        "contribute.submitting": "Mengirim...",
        "contribute.successMsg": "Dikirim untuk ditinjau!",
        "contribute.failedGeneric": "Pengiriman gagal"
    }
};

let currentUILang = localStorage.getItem(UI_LANG_STORAGE_KEY) || DEFAULT_UI_LANG;
if (!translations[currentUILang]) currentUILang = DEFAULT_UI_LANG;

function t(key, vars) {
    const dict = translations[currentUILang] || translations[DEFAULT_UI_LANG];
    let str = dict[key] ?? translations[DEFAULT_UI_LANG][key] ?? key;
    if (vars) {
        Object.keys(vars).forEach(k => {
            str = str.replace(new RegExp('{{' + k + '}}', 'g'), vars[k]);
        });
    }
    return str;
}

function applyTranslations(root) {
    root = root || document;
    root.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.getAttribute('data-i18n'));
    });
    root.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
    });
    root.querySelectorAll('[data-i18n-title]').forEach(el => {
        el.title = t(el.getAttribute('data-i18n-title'));
    });
    if (root === document) document.title = t('appTitle');
}

function getUILang() {
    return currentUILang;
}

function setUILang(lang) {
    if (!translations[lang]) return;
    currentUILang = lang;
    localStorage.setItem(UI_LANG_STORAGE_KEY, lang);
    document.documentElement.setAttribute('lang', lang);
    applyTranslations();

    const langSelect = document.getElementById('lang-select');
    if (langSelect && langSelect.value !== lang) langSelect.value = lang;

    document.dispatchEvent(new CustomEvent('uilangchange', { detail: { lang } }));
}

document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.setAttribute('lang', currentUILang);
    applyTranslations();

    const langSelect = document.getElementById('lang-select');
    if (langSelect) {
        langSelect.value = currentUILang;
        langSelect.addEventListener('change', () => setUILang(langSelect.value));
    }
});

window.t                = t;
window.getUILang        = getUILang;
window.setUILang        = setUILang;
window.applyTranslations = applyTranslations;
