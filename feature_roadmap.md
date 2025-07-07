<!-- 
=====================================================
IMPORTANT: This file is a REQUIRED component of The Oracle project.
This roadmap defines the feature development path and should NOT be moved to archived.
It serves as the development guide for implementing new features.
=====================================================
-->

### **Tier 1: Foundation & Core Usability (The MVP & Version 1.0)**

**Goal:** Build a stable, fast, and highly effective personal chat client that excels at the fundamentals. This tier focuses on making the day-to-day user experience seamless and powerful.

---

#### **Stage 1: The Bare Essentials (MVP)**

*Objective: Create a functional and reliable application that users can depend on for basic interactions.*

* **Core UI & Interaction:**
  * **[#4] "Copy Message" and "Copy Code" Buttons:** ✅ Add a small "copy" icon that appears on hover for each message bubble. For code blocks, a dedicated "Copy Code" button should appear at the top-right, copying only the code content without backticks.
  * **[#8] Clearer "New Chat" State:** ✅ When "New Chat" is clicked, replace the chat view with a welcome screen showing the selected model, quick-start buttons (e.g., "Explain Code," "Write an Email"), and perhaps some example prompts.
  * **[#12] Link Highlighting and Clicking:** ✅ Automatically detect URLs in the chat output and make them clickable, opening in the system's default browser.
  * **[#13] Markdown Table Rendering:** ✅ Improve the Markdown parser to properly render tables with correct alignment and borders, rather than just as plain text.
  * **[#25] "Scroll to Bottom" Button:** ✅ When the user scrolls up in the chat history, a "Scroll to Bottom" button should appear, allowing a quick return to the latest message.
  * **[#46] Background Auto-Save:** ✅ Automatically save the conversation to disk every few minutes or after every new message, preventing data loss on crash.
  * **[#55] Per-Conversation Model Association:** ✅ Remember which model was used for a specific conversation. When loading it, automatically switch the provider/model dropdowns to match.
* **Basic Conversation Management:**
  * **[#33] Rename Conversations:** ✅ A right-click option on a conversation in the list to rename it from the default summary to something more descriptive.
  * **[#50] Sort Conversation List:** ✅ Added sort options (by name, creation date, last modified) to the conversation list UI and implemented sorting logic.
* **Essential Settings:**
  * **[#63] Custom Ollama Host/Port:** ✅ Users can now set a custom Ollama host/port in the API settings dialog; the client uses this value for connections.
  * **[#68] Secure API Key Storage:** ✅ API keys are now stored and retrieved using the system keychain via the keyring library, not plain text files.
  * **[#77] API Key Validation:** ✅ When entering an API key, a test API call is made to validate it, with feedback shown in the settings dialog.
  * **[#173] Set Default Provider and Model:** ✅ Users can set default provider/model in settings; these are selected automatically on startup.
  * **[#190] "About The Oracle" Dialog:** ✅ Added Help > About menu with dialog showing version, license, repo, and dependencies.

#### **Stage 2: Enhanced Interaction & Management**

*Objective: Improve the conversational flow and give users better tools to organize their chats.*

* **Improved Chat Experience:**
  * **[#1] Threaded Replies:** ✅ Added context menu for messages with threaded reply, reply dialog, parent/child logic, and basic threaded rendering.
  * **[#2] Pin Messages in a Conversation:** ✅ Pin/unpin logic and UI (pin icon in chat display) implemented and improved.
  * **[#3] Edit User's Last Prompt:** ✅ Already implemented (edit_last_prompt method).
  * **[#7] In-conversation Search & Highlight:** ✅ Enhanced to highlight matches in chat display with real HTML highlighting.
  * **[#9] Message Timestamps:** ✅ Optional timestamps for each message bubble, toggleable in View menu.
  * **[#24] Token Count Display:** ✅ Real-time token count shown near input box (see show_token_count method).
* **Conversation Organization:**
  * **[#31] Folders for Conversations:** ✅ Users can create folders in the conversation list to organize chats.
  * **[#34] Search/Filter Conversation List:** ✅ Added search bar above conversation list to quickly find a chat by title or content.
  * **[#37] Archive Conversations:** ✅ Archive option hides conversations from main list but keeps them accessible in 'Archived' view.
  * **[#45] Pin Conversations to Top of List:** ✅ Pin important conversations to always appear at the top of the conversation list.
* **Performance:**
  * **[#191] Lazy Loading of Conversations:** ✅ Only loads conversation metadata for the sidebar at startup; full content is loaded from disk only when a conversation is clicked, with batch loading and a "Load More" button for large lists.
  * **[#192] Virtual Scrolling for Chat:** ✅ For long conversations, only the visible messages are rendered in the chat display, keeping the UI fast and responsive even with thousands of messages.
  
#### **Stage 3: The Coder's Toolkit**

*Objective: Add high-value features specifically for developers, a core user group.*

* **Code-centric Features:**
  * **[#23] Syntax Highlighting in Input Box:** ✅ Real-time syntax highlighting is applied in the input field when typing code blocks.
  * **[#82] "Save to File" Button on Code Blocks:** ✅ Added a "Save As..." button next to the copy button on code blocks, allowing direct export of code snippets.
  * **[#89] Automatic File Organization:** ✅ Code block exports are now saved in a subfolder under `exports` named after the conversation ID for better organization.
  * **[#106] "Open in Editor" button:** ✅ Saved code files now have an "Open in Editor" button to launch them in the user's default code editor.
  * **[#159] Code Quality Metrics:** ✅ Generated code is run through a linter (e.g., pylint/flake8) and quality feedback is displayed in the UI.
  * **[#254] Code Block Line Numbering:** An optional toggle to show line numbers inside code blocks for easier reference.
  * **[#255] Code Folding:** The ability to collapse/expand functions or classes within large code blocks directly in the chat view.
  * **[#771] CSV/Excel to Markdown Table:** Drag a CSV or Excel file onto the app, and it will be converted into a Markdown table in the input box.
* **Model & Prompting for Coders:**
  * **[#56] Model Parameter Sliders (Temperature, Top-p):** Expose common model parameters like Temperature, Top-p, and max tokens in a "Model Settings" panel, allowing for fine-grained control over generation.
  * **[#94] Diff Viewer for Code:** If the user asks the AI to "refactor" or "change" a piece of code, the app could show a side-by-side or inline diff of the changes.

#### **Stage 4: Power Prompting & Customization**

*Objective: Empower users to engineer better prompts and tailor the application to their needs.*

* **Prompt Engineering Tools:**
  * **[#18] Per-conversation System Prompt:** Allow the user to set a specific system prompt/persona for each conversation, which is stored and automatically applied every time that conversation is loaded.
  * **[#111] Prompt Library:** A user-curated library of favorite or effective prompts, organized by category, that can be inserted into the chat with one click.
  * **[#112] Prompt Templates with Variables:** Create prompt templates with placeholders (e.g., "Summarize the following text for a {{audience}}: {{text_to_summarize}}"), The UI would then present fields for the user to fill in.
  * **[#117] Slash Commands:** Pre-defined shortcuts for common actions, like `/summarize` to summarize the last response, `/clear` to clear context, or `/system` to change the system prompt mid-conversation.
  * **[#119] Prompt History Dropdown:** A history of the last 20 prompts sent by the user, accessible via a dropdown or arrow keys in the input box.
  * **[#121] Character/Persona Gallery:** A pre-populated gallery of system prompts for different characters (e.g., "Shakespearean Poet," "Helpful Rubber Duck," "Expert C++ Developer") that can be activated with one click.
* **UI Customization:**
  * **[#10] Customizable UI Fonts & Sizes:** In settings, allow the user to select the font family and font size for both the chat display and the input box, improving accessibility.
  * **[#166] Theme Editor/Importer:** A built-in editor to create and save custom QSS themes. Users could also import/export theme files to share them.
  * **[#172] Keyboard Shortcut Editor:** Allow users to customize keyboard shortcuts for common actions like "New Chat," "Send Message," etc.
  * **[#186] Compact vs. Spacious UI Mode:** A toggle in the View menu to adjust padding and margins for either a more dense, information-rich display or a more spacious, readable one.

---

### **Tier 2: Advanced Features & Multimodality**

**Goal:** Expand beyond a text-only client into a versatile "power tool" that can handle different types of media and perform deeper analysis.

---

#### **Stage 5: Multimodality - Vision & Audio**

*Objective: Integrate vision and audio capabilities to handle a wider range of inputs.*

* **Vision Models:**
  * **[#87] Vision Model Integration (True File Attachment):** Fully integrate with vision models (like LLaVA or Gemini Pro Vision). Users could drag-and-drop images into the chat, and the image data would be sent along with the prompt.
  * **[#103] File Attachment via Drag and Drop:** Support dragging a file from the desktop directly onto the chat window to attach it.
  * **[#104] Image Paste from Clipboard:** Allow pasting an image directly from the clipboard into the input area for vision models.
  * **[#839] Chart and Plot Explainer:** Attach an image of a chart, and the AI will describe what the chart shows, identify the trend, and point out any anomalies.
* **Audio Models:**
  * **[#90] Audio Transcription (Whisper):** Allow the user to drop an audio file into the chat. The app would use a model like Whisper to transcribe it, and the transcript would appear as a user message.
  * **[#91] Text-to-Speech for Responses:** Add a "Read Aloud" button for each AI response, using a TTS engine to speak the message.
  * **[#123] Voice-to-Text Input:** Use the system's microphone to dictate prompts, which are transcribed into the input box in real-time.
* **UI for Attachments:**
  * **[#88] View & Manage Attachments:** A side panel that lists all files attached to the current conversation, allowing users to preview or remove them.

#### **Stage 6: RAG & Knowledge Management**

*Objective: Give the application a memory by implementing Retrieval-Augmented Generation (RAG) on local files.*

* **RAG Core:**
  * **[#136] Local Document RAG:** A dedicated "Knowledge Base" UI where users can upload documents (.pdf, .txt, .md, .docx). The app chunks and embeds these documents into a vector store (like FAISS or LanceDB).
  * **[#137] Toggleable RAG for Prompts:** ✅ Added a checkbox next to the send button to enable/disable RAG; when checked, relevant knowledge base chunks are included in the prompt.
  * **[#138] View RAG Sources:** ✅ When RAG is used, the UI displays which document chunks were used as sources for the response.
  * **[#155] RAG Chunking Strategy Controls:** ✅ Users can configure RAG chunk size, overlap, and embedding model in the knowledge base settings.
* **Advanced Search & Analysis:**
  * **[#141] Semantic Search Across All Conversations:** ✅ Added a global semantic search bar using vector embeddings to find related conversations by meaning, not just keywords.
  * **[#788] RAG for Codebases:** ✅ Users can index an entire source code repository for RAG, enabling codebase-wide questions and retrieval.
  * **[#789] Cross-conversation Topic Clustering:** A visualization that groups all your conversations into thematic clusters, helping you discover overarching themes in your work.

#### **Stage 7: Professional Output & Interactivity**

*Objective: Enhance output options for professional use cases and begin introducing interactive content.*

* **Professional Exports:**
  * **[#83] Improved PDF Export:** When exporting to PDF, use a library that preserves formatting, code highlighting, and images, creating a high-fidelity, professional-looking document.
  * **[#84] Markdown Export:** Add an option to export the chat to a clean, well-formatted Markdown (`.md`) file.
  * **[#95] Export Selection to File:** Allow the user to select multiple messages and export only that selection to any of the available formats (TXT, JSON, MD).
  * **[#389] DOCX/Google Docs Export:** A more powerful export that converts the chat into a well-structured document, using headings for prompts and blockquotes for responses.
  * **[#775] Powerpoint Presentation Generator:** A command (`/create_slides`) that takes an outline and generates a basic `.pptx` file with one slide per bullet point.
* **Interactive Outputs:**
  * **[#92] Data-Structure Formatting:** If the AI outputs a JSON or YAML object, automatically format it with syntax highlighting and make it collapsible.
  * **[#97] LaTeX Rendering:** Support rendering of mathematical formulas written in LaTeX (e.g., between `$...$` or `$$...$$`) using a library like KaTeX.
  * **[#342] Render Interactive Matplotlib/Plotly Charts:** Instead of a static image, the AI's Python code can generate interactive plots (with hover-to-see-values, zoom, pan) that are displayed directly in the chat.
  * **[#348] Mind Map Generation:** The AI outputs a mind map in a format like PlantUML or Mermaid, and the application renders it as a navigable, interactive diagram.

#### **Stage 8: Automation & Workflow Engine V1**

*Objective: Introduce features that allow users to chain commands and automate repetitive tasks.*

* **Automation Primitives:**
  * **[#81] Execute Code Blocks (Sandboxed):** Add a "Run" button to code blocks. When clicked, execute the code in a secure, isolated environment (e.g., Docker container, firejail) and display the output (`stdout`, `stderr`) directly below the block.
  * **[#116] Chained Prompts / Workflows:** A simple workflow builder where a user can chain prompts together (e.g., "Step 1: Draft a blog post from these bullet points. Step 2: Take the output of Step 1 and generate 5 title options.").
  * **[#118] Automatic "Continue" Prompting:** If a model's output is cut short due to max token limits, add a "Continue" button that automatically sends a prompt like "Please continue from where you left off."
  * **[#130] Auto-Retry on Failure:** If an API call fails due to a temporary network error or rate limit, the application should automatically retry the request 1-2 times with exponential backoff.
  * **[#781] Visual Prompt Builder (Node-based):** A separate interface where you can build a prompt by connecting nodes (e.g., "Load File" -> "Summarize Text" -> "Format as Email"), which then compiles down to a single, complex prompt.
* **Integration (Early Steps):**
  * **[#99] Handle Multi-file Codebases:** Allow the app to read all files in a directory and provide them as context to the LLM, enabling questions about an entire codebase.
  * **[#379] Local Shell Command Execution:** A `/shell` command to securely run a shell command and feed its `stdout` back into the conversation. (Requires strict security warnings!).

---

### **Tier 3: Platform Extensibility & Specialization**

**Goal:** Transform the application from a standalone tool into an extensible platform that integrates deeply with other services and the user's operating system.

---

#### **Stage 9: The Plugin Platform**

*Objective: Create a robust plugin system to enable community-driven feature development.*

* **Core Plugin Architecture:**
  * **[#206] Plugin System:** A full-fledged plugin system allowing third-party developers to add new features, like new API providers, custom UI panels, or new export formats.
  * **[#215] Event Bus for Plugins:** A well-documented event bus that plugins can subscribe to (e.g., `on_new_message`, `on_model_change`) to build event-driven features.
  * **[#408] Granular Permissions System for Plugins:** When installing a plugin, it must explicitly request permissions (e.g., "This plugin wants to access the network," "This plugin wants to read your files"), which the user must approve.
  * **[#214] Plugin Marketplace:** A UI within the app to browse, install, and manage plugins from a central repository.
  * **[#802] Custom Web-based UI Panels (via Plugins):** A plugin API that allows developers to add new panels to the main UI using HTML/JS/CSS, rendered in a QWebEngineView.
* **Developer Support:**
  * **[#217] Debug Mode for API Calls:** A toggle that logs the full, raw JSON request and response for every API call, helping developers debug issues with prompts or providers.
  * **[#224] Hot-reloading for Plugin Development:** When developing a plugin, have the application automatically reload it when its source files change.

#### **Stage 10: Deep OS Integration**

*Objective: Break the application out of its window and integrate it with the user's wider computing environment.*

* **System-wide Tools:**
  * **[#371] System-wide Quick Capture:** ✅ Added a global hotkey to open a quick input window from anywhere in the OS to send prompts to Oracle.
  * **[#817] AI-powered Shell Companion (`aicmd`):** ✅ Included a command-line tool (`aicmd`) to pipe shell output to Oracle for instant explanations in the terminal.
  * **[#818] "Smart Clipboard" Daemon:** ✅ Background process monitors clipboard for code/errors and provides instant documentation or solutions via system notifications.
  * **[#373] Browser Extension:** ✅ Companion browser extension allows right-clicking text/images to send to Oracle or summarize the current page.
* **File System & Automation:**
  * **[#816] File System Automation:** ✅ UI for creating file automation rules (e.g., auto-summarize new .docx files in Downloads) is now available.
  * **[#820] Natural Language File Search:** A search window (like Spotlight or Alfred) where you can type "find the presentation I made about marketing last month," and the AI will translate that into a complex file system query and return the results.
  * **[#821] Application Automation/Scripting:** The AI can generate and execute scripts for OS-level automation tools like AppleScript, JXA (JavaScript for Automation), or Power Automate.


