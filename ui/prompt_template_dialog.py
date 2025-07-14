"""
Comprehensive Prompt Builder Dialog
A structured form for creating effective prompts by filling out all required components:
- Instructions/Task: What you want the AI to do
- Context/Input: The information/data to work with
- Persona/Role: What role the AI should take
- Examples: Sample inputs/outputs to guide the AI
- Output Format/Tone: How the response should be structured and styled
- Constraints: Limitations, requirements, and guidelines

Enhanced Template Library: 40+ Professional Templates across 11 categories:
- Business & Strategy (Business plans, market research, brand strategy)
- Content & Marketing (Blog posts, social media, email campaigns)
- Education & Training (Course design, manuals, tutorials)
- Technical & Development (API docs, code documentation, specs)
- Research & Analysis (Research papers, surveys, data analysis)
- Creative & Design (Creative briefs, UX design, copywriting)
- Professional & Career (Resumes, cover letters, performance reviews)
- Customer Service (Support responses, FAQs, user manuals)
- Sales & Marketing (Proposals, strategies, product launches)
- Problem Solving (Decision making, process improvement)
- Code Review & Development (Code reviews, architecture, databases)

New Feature: AI-Assisted Generation
- Users can leave sections blank and use "Generate Missing Sections" to have AI fill them
- The AI analyzes filled sections to generate contextually appropriate content for empty ones
- Ensures narrative consistency and coherence across all sections
"""

from typing import Dict, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QScrollArea, QWidget,
                             QGroupBox, QInputDialog, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from .theme_styles import get_dialog_theme_styles, create_themed_message_box, get_icon_path


class PromptTemplateDialog(QDialog):
    """Dialog for creating comprehensive prompts using a structured framework"""


    def __init__(self, parent=None, dark_theme=True, multi_client=None):
        super().__init__(parent)
        self.dark_theme = dark_theme
        self.multi_client = multi_client
        self.setWindowTitle("Prompt Framework - Create Effective Prompts (40+ Templates)")
        self.setMinimumSize(1000, 800)
        self.resize(1200, 900)

        # Set window icon
        icon_path = get_icon_path("chat", "chat")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        # Initialize the prompt framework sections
        self.framework_sections = self.get_framework_sections()
        self.section_widgets = {}

        self.setup_ui()
        self.apply_theme_styles()

    def get_framework_sections(self) -> Dict[str, Dict[str, Any]]:
        """Get the framework sections with descriptions and examples"""
        return {
            "instructions": {
                "title": "📋 Instructions / Task",
                "description": "Clearly define what you want the AI to do. Be specific about the action, scope, and desired outcome.",
                "placeholder": "Example: Analyze the provided data and create a comprehensive report...",
                "examples": [
                    "Analyze the customer feedback data and identify key themes",
                    "Write a professional email responding to a customer complaint",
                    "Create a step-by-step tutorial for setting up a development environment",
                    "Review the code and suggest improvements for performance and readability"
                ]
            },
            "context": {
                "title": "🔍 Context / Input",
                "description": "Provide the information, data, or background the AI needs to complete the task.",
                "placeholder": "Example: Here is the dataset/document/information to work with...",
                "examples": [
                    "Customer feedback data: [CSV data or survey responses]",
                    "Customer complaint: [Original complaint text]",
                    "Technology stack: Python, Flask, PostgreSQL, Docker",
                    "Code to review: [Code snippet or file]"
                ]
            },
            "persona": {
                "title": "🎭 Persona / Role",
                "description": "Define what role or expertise the AI should adopt. This shapes the perspective and approach.",
                "placeholder": "Example: Act as a senior data analyst with 10 years of experience...",
                "examples": [
                    "Act as a senior data analyst with expertise in customer experience",
                    "Respond as a professional customer service manager",
                    "Take the role of an experienced software developer and mentor",
                    "Act as a technical writer specializing in developer documentation"
                ]
            },
            "examples": {
                "title": "💡 Examples",
                "description": "Provide examples of good inputs/outputs to guide the AI's understanding and response style.",
                "placeholder": "Example: Here are some similar cases and how they were handled...",
                "examples": [
                    "Similar analysis example: [Show format and depth expected]",
                    "Sample professional email response: [Template or example]",
                    "Good tutorial example: [Link or excerpt from quality tutorial]",
                    "Quality code review example: [Show constructive feedback style]"
                ]
            },
            "output_format": {
                "title": "📄 Output Format / Tone",
                "description": "Specify how the response should be structured, formatted, and what tone to use.",
                "placeholder": "Example: Provide a formal report with executive summary, findings, and recommendations...",
                "examples": [
                    "Formal report with: Executive Summary, Key Findings, Recommendations",
                    "Professional, empathetic tone with clear action items",
                    "Step-by-step numbered list with code examples and explanations",
                    "Structured feedback with: Strengths, Issues, Specific Improvements"
                ]
            },
            "constraints": {
                "title": "⚠️ Constraints / Requirements",
                "description": "Define limitations, requirements, guidelines, and what to avoid.",
                "placeholder": "Example: Keep response under 500 words, avoid technical jargon...",
                "examples": [
                    "Maximum 2 pages, focus on actionable insights only",
                    "Maintain professional tone, provide specific resolution steps",
                    "Include code examples, assume intermediate programming knowledge",
                    "Focus on practical improvements, include performance impact estimates"
                ]
            }
        }

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Title and description
        title_label = QLabel("🎯 Prompt Framework - Build Effective Prompts")
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)

        description = QLabel(
            "Create comprehensive prompts by filling out all sections below. Each section is essential for guiding the AI to provide the best possible response. Use 'Load Template' to choose from 40+ professional templates across 11 categories."
        )
        description.setObjectName("description_label")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create form widget
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(20)

        # Create sections
        self.setup_framework_sections(form_layout)

        scroll_area.setWidget(form_widget)
        layout.addWidget(scroll_area)

        # Preview area
        self.setup_preview_area(layout)

        # Buttons
        self.setup_buttons(layout)

    def setup_framework_sections(self, layout):
        """Create the framework sections"""
        for section_key, section_info in self.framework_sections.items():
            group = QGroupBox(section_info["title"])
            group.setObjectName("framework_group")
            group_layout = QVBoxLayout(group)

            # Description
            desc_label = QLabel(section_info["description"])
            desc_label.setObjectName("section_description")
            desc_label.setWordWrap(True)
            group_layout.addWidget(desc_label)

            # Examples button
            examples_btn = QPushButton("💡 Show Examples")
            examples_btn.setObjectName("examples_button")
            examples_btn.clicked.connect(lambda checked, key=section_key: self.show_examples(key))
            examples_btn.setMaximumWidth(150)
            group_layout.addWidget(examples_btn)

            # Text input
            text_edit = QTextEdit()
            text_edit.setObjectName("section_input")
            text_edit.setPlaceholderText(section_info["placeholder"])
            text_edit.setMaximumHeight(120)
            text_edit.textChanged.connect(self.update_preview)

            self.section_widgets[section_key] = text_edit
            group_layout.addWidget(text_edit)

            layout.addWidget(group)

    def setup_preview_area(self, layout):
        """Setup the preview area"""
        preview_group = QGroupBox("📋 Generated Prompt Preview")
        preview_group.setObjectName("preview_group")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_text = QTextEdit()
        self.preview_text.setObjectName("preview_text")
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setPlaceholderText("Your generated prompt will appear here as you fill out the sections above...")
        preview_layout.addWidget(self.preview_text)

        layout.addWidget(preview_group)

    def setup_buttons(self, layout):
        """Setup the button layout"""
        button_layout = QHBoxLayout()

        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.setObjectName("clear_button")
        clear_btn.clicked.connect(self.clear_all_sections)
        button_layout.addWidget(clear_btn)

        template_btn = QPushButton("📋 Load Template (40+ Available)")
        template_btn.setObjectName("template_button")
        template_btn.clicked.connect(self.load_template)
        button_layout.addWidget(template_btn)

        # Add generate button if multi_client is available
        if self.multi_client:
            generate_btn = QPushButton("🪄 Generate Missing Sections")
            generate_btn.setObjectName("generate_button")
            generate_btn.clicked.connect(self.generate_missing_sections)
            button_layout.addWidget(generate_btn)

        button_layout.addStretch()

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setObjectName("copy_button")
        copy_btn.clicked.connect(self.copy_prompt)
        button_layout.addWidget(copy_btn)

        use_btn = QPushButton("✅ Use This Prompt")
        use_btn.setObjectName("use_button")
        use_btn.clicked.connect(self.use_prompt)
        use_btn.setDefault(True)
        button_layout.addWidget(use_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setObjectName("cancel_button")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def show_examples(self, section_key):
        """Show examples for a specific section"""
        if section_key not in self.framework_sections:
            return

        section_info = self.framework_sections[section_key]
        examples_text = "\n\n".join([f"• {example}" for example in section_info["examples"]])

        message = f"Examples for {section_info['title']}:\n\n{examples_text}"

        create_themed_message_box(
            self, f"Examples - {section_info['title']}",
            message,
            "info",
            self.dark_theme
        ).exec()

    def update_preview(self):
        """Update the preview as user types"""
        prompt_parts = []

        for section_key, section_info in self.framework_sections.items():
            if section_key in self.section_widgets:
                text_widget = self.section_widgets[section_key]
                content = text_widget.toPlainText().strip()

                if content:
                    prompt_parts.append(f"{section_info['title']}\n{content}")

        if prompt_parts:
            final_prompt = "\n\n".join(prompt_parts)
        else:
            final_prompt = "Fill out the sections above to see your prompt preview..."

        self.preview_text.setPlainText(final_prompt)

    def clear_all_sections(self):
        """Clear all input sections"""
        for widget in self.section_widgets.values():
            widget.clear()
        self.update_preview()

    def load_template(self):
        """Load a predefined template"""
        templates = {
            # === BUSINESS & STRATEGY ===
            "Business Plan": {
                "instructions": "Create a comprehensive business plan with market analysis, financial projections, and strategic recommendations.",
                "context": "Business Type: [Specify your business idea] Market: [Target market description] Stage: [Startup/Expansion/Pivot]",
                "persona": "Act as a seasoned business consultant with expertise in strategic planning and market analysis.",
                "examples": "Include market size analysis, competitive landscape, revenue projections, and risk assessment similar to successful business plans.",
                "output_format": "Structure as: Executive Summary, Market Analysis, Business Model, Financial Projections, Marketing Strategy, and Implementation Timeline.",
                "constraints": "Focus on realistic assumptions and measurable goals. Include 3-5 year projections. Keep financial details specific and actionable."
            },
            "Market Research": {
                "instructions": "Conduct comprehensive market research to identify opportunities, threats, and competitive positioning.",
                "context": "Industry: [Specify industry] Target Market: [Demographics/geography] Product/Service: [What you're researching]",
                "persona": "Act as a market research analyst with expertise in consumer behavior and industry trends.",
                "examples": "Include competitor analysis, market size estimation, consumer insights, and trend identification.",
                "output_format": "Present findings in: Market Overview, Competitive Analysis, Consumer Insights, Opportunities & Threats, and Strategic Recommendations.",
                "constraints": "Base conclusions on credible sources and data. Highlight actionable insights. Maximum 3 pages with visual data representation."
            },
            "Brand Strategy": {
                "instructions": "Develop a comprehensive brand strategy including positioning, messaging, and visual identity guidelines.",
                "context": "Company: [Company name/description] Industry: [Industry sector] Target Audience: [Customer demographics]",
                "persona": "Act as a brand strategist with expertise in brand development and market positioning.",
                "examples": "Include brand positioning statement, messaging framework, visual identity guidelines, and brand activation strategies.",
                "output_format": "Structure as: Brand Positioning, Brand Personality, Messaging Framework, Visual Identity, and Implementation Guidelines.",
                "constraints": "Ensure brand consistency across all touchpoints. Focus on differentiation and emotional connection. Include practical implementation steps."
            },
            "SWOT Analysis": {
                "instructions": "Conduct a comprehensive SWOT analysis to evaluate internal strengths/weaknesses and external opportunities/threats.",
                "context": "Organization: [Company/project name] Industry: [Industry context] Scope: [Analysis scope/timeframe]",
                "persona": "Act as a strategic business analyst with expertise in organizational assessment and strategic planning.",
                "examples": "Include specific examples for each SWOT category with strategic implications and actionable insights.",
                "output_format": "Present as: Strengths (internal positives), Weaknesses (internal negatives), Opportunities (external positives), Threats (external negatives), and Strategic Recommendations.",
                "constraints": "Be specific and evidence-based. Focus on actionable items. Link each element to strategic implications and next steps."
            },

            # === CONTENT & MARKETING ===
            "Blog Post": {
                "instructions": "Write an engaging and informative blog post that provides value to readers and drives engagement.",
                "context": "Topic: [Blog topic] Target Audience: [Reader demographics] Purpose: [Inform/educate/entertain/convert]",
                "persona": "Act as an experienced content writer with expertise in SEO and audience engagement.",
                "examples": "Include compelling headlines, subheadings, actionable tips, and relevant examples that resonate with the target audience.",
                "output_format": "Structure as: Compelling headline, Introduction with hook, Main content with subheadings, Conclusion with call-to-action, and SEO considerations.",
                "constraints": "Optimize for SEO with relevant keywords. Keep paragraphs short and scannable. Include internal/external links. 800-1500 words."
            },
            "Social Media Campaign": {
                "instructions": "Design a comprehensive social media campaign strategy with content calendar and engagement tactics.",
                "context": "Platform(s): [Social media platforms] Campaign Goal: [Awareness/engagement/conversion] Duration: [Campaign length]",
                "persona": "Act as a social media marketing specialist with expertise in content strategy and audience engagement.",
                "examples": "Include post types, hashtag strategies, engagement techniques, and successful campaign examples from similar industries.",
                "output_format": "Present as: Campaign Overview, Content Calendar, Post Examples, Engagement Strategy, and Performance Metrics.",
                "constraints": "Platform-specific content optimization. Include visual content suggestions. Focus on measurable KPIs. 2-4 weeks of detailed planning."
            },
            "Email Marketing": {
                "instructions": "Create an effective email marketing campaign with compelling subject lines, content, and call-to-actions.",
                "context": "Campaign Type: [Newsletter/promotional/nurture] Audience: [Subscriber demographics] Goal: [Engagement/conversion/retention]",
                "persona": "Act as an email marketing specialist with expertise in conversion optimization and subscriber engagement.",
                "examples": "Include subject line variations, personalization techniques, and successful email examples with high open/click rates.",
                "output_format": "Structure as: Subject Line Options, Email Content, Call-to-Action Strategy, A/B Testing Plan, and Success Metrics.",
                "constraints": "Ensure mobile optimization. Include personalization elements. Focus on clear CTAs. Comply with email marketing regulations."
            },
            "SEO Content": {
                "instructions": "Create SEO-optimized content that ranks well in search engines while providing genuine value to readers.",
                "context": "Target Keywords: [Primary and secondary keywords] Content Type: [Article/guide/review] Search Intent: [Informational/commercial/navigational]",
                "persona": "Act as an SEO content specialist with expertise in search engine optimization and content marketing.",
                "examples": "Include keyword integration examples, meta descriptions, internal linking strategies, and content structures that rank well.",
                "output_format": "Present as: SEO-optimized headline, Meta description, Content outline with keyword placement, Internal linking suggestions, and Technical SEO recommendations.",
                "constraints": "Natural keyword integration. Focus on user experience. Include related keywords and semantic terms. 1000-2000 words for comprehensive coverage."
            },

            # === EDUCATION & TRAINING ===
            "Course Curriculum": {
                "instructions": "Design a comprehensive course curriculum with learning objectives, modules, and assessment methods.",
                "context": "Subject: [Course topic] Audience: [Student demographics/skill level] Duration: [Course length] Format: [Online/in-person/hybrid]",
                "persona": "Act as an instructional designer with expertise in curriculum development and adult learning principles.",
                "examples": "Include module breakdown, learning activities, assessment methods, and successful course structures from similar subjects.",
                "output_format": "Structure as: Course Overview, Learning Objectives, Module Breakdown, Assessment Strategy, and Resource Requirements.",
                "constraints": "Align with learning objectives. Include diverse learning activities. Progressive skill building. Measurable outcomes for each module."
            },
            "Training Manual": {
                "instructions": "Create a comprehensive training manual with step-by-step instructions, examples, and exercises.",
                "context": "Training Topic: [Skill/process to be learned] Audience: [Employee level/department] Application: [Work context/environment]",
                "persona": "Act as a training specialist with expertise in adult learning and skill development.",
                "examples": "Include clear procedures, visual aids, practice exercises, and real-world scenarios that reinforce learning.",
                "output_format": "Present as: Training Objectives, Step-by-step Procedures, Practice Exercises, Troubleshooting Guide, and Assessment Checklist.",
                "constraints": "Use clear, jargon-free language. Include visual elements. Progressive complexity. Immediate application opportunities."
            },
            "Tutorial Guide": {
                "instructions": "Write a clear, step-by-step tutorial that guides users through a complex process or skill.",
                "context": "Tutorial Topic: [What you're teaching] User Level: [Beginner/intermediate/advanced] Goal: [What users will accomplish]",
                "persona": "Act as a technical writer with expertise in creating user-friendly instructional content.",
                "examples": "Include screenshots, code examples, troubleshooting tips, and common mistakes to avoid.",
                "output_format": "Structure as: Prerequisites, Step-by-step Instructions, Visual Aids, Troubleshooting, and Next Steps.",
                "constraints": "Test all steps for accuracy. Include alternative approaches. Clear navigation. Assume no prior knowledge for beginner content."
            },
            "Assessment Design": {
                "instructions": "Create comprehensive assessments that accurately measure learning outcomes and provide meaningful feedback.",
                "context": "Subject Area: [Assessment topic] Assessment Type: [Quiz/exam/project/portfolio] Audience: [Student level/context]",
                "persona": "Act as an assessment specialist with expertise in educational measurement and learning evaluation.",
                "examples": "Include various question types, rubrics, performance indicators, and feedback mechanisms.",
                "output_format": "Present as: Assessment Overview, Question Bank, Scoring Rubric, Feedback Framework, and Improvement Recommendations.",
                "constraints": "Align with learning objectives. Include various difficulty levels. Provide constructive feedback. Fair and unbiased assessment methods."
            },

            # === TECHNICAL & DEVELOPMENT ===
            "API Documentation": {
                "instructions": "Create comprehensive API documentation that enables developers to easily integrate and use the API.",
                "context": "API Type: [REST/GraphQL/other] Functionality: [What the API does] Audience: [Developer experience level]",
                "persona": "Act as a technical writer with expertise in API documentation and developer experience.",
                "examples": "Include endpoint descriptions, request/response examples, authentication methods, and error handling.",
                "output_format": "Structure as: Getting Started, Authentication, Endpoints, Request/Response Examples, Error Codes, and SDKs.",
                "constraints": "Include working code examples. Clear error messages. Version information. Rate limiting details. Interactive examples where possible."
            },
            "Code Documentation": {
                "instructions": "Write clear, comprehensive code documentation that helps developers understand and maintain the codebase.",
                "context": "Code Type: [Application/library/framework] Language: [Programming language] Complexity: [Simple/moderate/complex]",
                "persona": "Act as a senior developer with expertise in code documentation and software architecture.",
                "examples": "Include function descriptions, parameter explanations, usage examples, and best practices.",
                "output_format": "Present as: Overview, Installation Guide, Usage Examples, API Reference, Contributing Guidelines, and Troubleshooting.",
                "constraints": "Keep documentation up-to-date with code. Include practical examples. Clear naming conventions. Version compatibility information."
            },
            "Technical Specification": {
                "instructions": "Create detailed technical specifications that guide development teams in building software systems.",
                "context": "System Type: [Web app/mobile app/API/other] Requirements: [Functional requirements] Constraints: [Technical constraints]",
                "persona": "Act as a system architect with expertise in technical specification writing and system design.",
                "examples": "Include system architecture diagrams, data models, API specifications, and security requirements.",
                "output_format": "Structure as: System Overview, Architecture Design, Technical Requirements, Data Models, Security Specifications, and Testing Strategy.",
                "constraints": "Be specific and measurable. Include non-functional requirements. Consider scalability and maintainability. Clear acceptance criteria."
            },
            "Bug Report": {
                "instructions": "Write a comprehensive bug report that helps developers quickly identify, reproduce, and fix issues.",
                "context": "Application: [Software/system name] Bug Type: [UI/functionality/performance/security] Severity: [Critical/high/medium/low]",
                "persona": "Act as a QA engineer with expertise in bug tracking and software testing.",
                "examples": "Include reproduction steps, expected vs actual behavior, screenshots, and system environment details.",
                "output_format": "Present as: Bug Summary, Reproduction Steps, Expected Behavior, Actual Behavior, Environment Details, and Additional Information.",
                "constraints": "Be specific and reproducible. Include relevant screenshots/logs. Priority and severity levels. Clear acceptance criteria for fix."
            },

            # === RESEARCH & ANALYSIS ===
            "Research Paper": {
                "instructions": "Write a comprehensive research paper with proper methodology, analysis, and evidence-based conclusions.",
                "context": "Research Topic: [Your research question] Field: [Academic/professional discipline] Scope: [Research scope and limitations]",
                "persona": "Act as a research scholar with expertise in academic writing and research methodology.",
                "examples": "Include literature review, methodology explanation, data analysis, and peer-reviewed references.",
                "output_format": "Structure as: Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, and References.",
                "constraints": "Follow academic standards. Cite credible sources. Peer-reviewed references. Logical argument flow. 3000-5000 words for comprehensive coverage."
            },
            "Literature Review": {
                "instructions": "Conduct a systematic literature review that synthesizes existing research on a specific topic.",
                "context": "Research Topic: [Topic area] Time Period: [Years to cover] Source Types: [Academic papers/books/reports]",
                "persona": "Act as an academic researcher with expertise in systematic review methodology and critical analysis.",
                "examples": "Include search strategy, inclusion criteria, thematic analysis, and research gaps identification.",
                "output_format": "Present as: Search Strategy, Inclusion Criteria, Thematic Analysis, Key Findings, Research Gaps, and Future Directions.",
                "constraints": "Systematic approach. Critical analysis. Identify patterns and gaps. Credible sources only. Minimum 20-30 relevant sources."
            },
            "Data Analysis": {
                "instructions": "Analyze the provided dataset and create a comprehensive report with key insights, trends, and actionable recommendations.",
                "context": "Dataset: [Provide your dataset or describe the data you want analyzed] Analysis Type: [Descriptive/inferential/predictive]",
                "persona": "Act as a senior data analyst with expertise in statistical analysis and business intelligence.",
                "examples": "Similar analysis should include: summary statistics, trend analysis, correlation findings, and business implications.",
                "output_format": "Provide a structured report with: Executive Summary, Key Findings, Detailed Analysis, Visualizations, and Recommendations.",
                "constraints": "Keep the analysis focused on business-relevant insights. Avoid overly technical jargon. Include data limitations. Maximum 2 pages."
            },
            "Survey Design": {
                "instructions": "Design a comprehensive survey that collects reliable and valid data to answer specific research questions.",
                "context": "Research Purpose: [What you want to learn] Target Population: [Survey respondents] Data Collection Method: [Online/phone/in-person]",
                "persona": "Act as a survey research specialist with expertise in questionnaire design and data collection methods.",
                "examples": "Include various question types, response scales, demographic questions, and bias reduction techniques.",
                "output_format": "Structure as: Survey Objectives, Question Design, Response Scales, Demographic Questions, and Data Collection Strategy.",
                "constraints": "Avoid leading questions. Include validation questions. Appropriate length (10-15 minutes). Clear instructions. Pilot testing recommendations."
            },

            # === CREATIVE & DESIGN ===
            "Creative Brief": {
                "instructions": "Create a comprehensive creative brief that guides the development of marketing materials and campaigns.",
                "context": "Project Type: [Campaign/design/video/etc.] Brand: [Brand information] Target Audience: [Audience demographics]",
                "persona": "Act as a creative director with expertise in brand communication and creative strategy.",
                "examples": "Include brand guidelines, mood boards, messaging frameworks, and successful creative references.",
                "output_format": "Present as: Project Overview, Brand Guidelines, Target Audience, Key Messages, Creative Direction, and Success Metrics.",
                "constraints": "Align with brand identity. Clear creative direction. Measurable objectives. Include inspiration references. Timeline considerations."
            },
            "UX Design": {
                "instructions": "Design a user experience strategy that creates intuitive and engaging digital interfaces.",
                "context": "Product Type: [Web app/mobile app/website] Users: [Target user demographics] Goals: [User and business objectives]",
                "persona": "Act as a UX designer with expertise in user-centered design and usability principles.",
                "examples": "Include user personas, user journey maps, wireframes, and usability testing recommendations.",
                "output_format": "Structure as: User Research, User Personas, User Journey Maps, Design Principles, Wireframes, and Testing Strategy.",
                "constraints": "Focus on user needs. Accessibility compliance. Mobile-first approach. Iterative design process. Usability testing integration."
            },
            "Video Script": {
                "instructions": "Write an engaging video script that captures attention and delivers key messages effectively.",
                "context": "Video Type: [Explainer/promotional/educational/testimonial] Duration: [Video length] Platform: [YouTube/social media/website]",
                "persona": "Act as a video scriptwriter with expertise in storytelling and audience engagement.",
                "examples": "Include hook techniques, visual descriptions, call-to-action strategies, and platform-specific considerations.",
                "output_format": "Present as: Hook/Opening, Main Content Outline, Visual Descriptions, Dialogue/Narration, and Call-to-Action.",
                "constraints": "Platform-appropriate length. Visual storytelling. Clear call-to-action. Engaging opening. Include timing notes."
            },
            "Copywriting": {
                "instructions": "Write compelling copy that persuades the target audience to take specific action.",
                "context": "Copy Type: [Sales page/ad/email/brochure] Product/Service: [What you're promoting] Audience: [Target customer profile]",
                "persona": "Act as a copywriter with expertise in persuasive writing and conversion optimization.",
                "examples": "Include headline variations, benefit statements, social proof elements, and urgency/scarcity techniques.",
                "output_format": "Structure as: Headline Options, Value Proposition, Benefit Statements, Social Proof, Objection Handling, and Call-to-Action.",
                "constraints": "Focus on benefits over features. Include social proof. Clear call-to-action. A/B testing recommendations. Compliance with advertising standards."
            },

            # === PROFESSIONAL & CAREER ===
            "Resume": {
                "instructions": "Create a professional resume that effectively showcases skills, experience, and achievements.",
                "context": "Industry: [Target industry] Role: [Position applying for] Experience Level: [Entry/mid/senior level]",
                "persona": "Act as a career counselor with expertise in resume writing and job market trends.",
                "examples": "Include achievement statements, skill keywords, formatting guidelines, and industry-specific requirements.",
                "output_format": "Present as: Professional Summary, Core Competencies, Work Experience, Education, and Additional Sections.",
                "constraints": "ATS-friendly format. Quantified achievements. Industry-relevant keywords. One page for entry-level, two pages maximum for senior roles."
            },
            "Cover Letter": {
                "instructions": "Write a compelling cover letter that demonstrates fit for the position and company culture.",
                "context": "Position: [Job title] Company: [Company name and culture] Background: [Relevant experience/skills]",
                "persona": "Act as a career coach with expertise in professional communication and job application strategies.",
                "examples": "Include personalization techniques, achievement highlights, company research integration, and professional tone.",
                "output_format": "Structure as: Opening Hook, Relevant Experience, Company Fit, Value Proposition, and Professional Closing.",
                "constraints": "Personalized to company and role. Specific achievements. Professional tone. One page maximum. Error-free writing."
            },
            "Performance Review": {
                "instructions": "Write a comprehensive performance review that provides constructive feedback and development guidance.",
                "context": "Employee: [Role/department] Review Period: [Time period] Performance Areas: [Key performance areas]",
                "persona": "Act as an HR professional with expertise in performance management and employee development.",
                "examples": "Include specific examples, balanced feedback, goal setting, and development planning.",
                "output_format": "Present as: Performance Summary, Strengths, Areas for Improvement, Goal Achievement, and Development Plan.",
                "constraints": "Balanced and constructive feedback. Specific examples. Clear development goals. Professional tone. Forward-looking recommendations."
            },
            "Job Description": {
                "instructions": "Create a comprehensive job description that attracts qualified candidates and sets clear expectations.",
                "context": "Position: [Job title] Department: [Department/team] Level: [Seniority level] Company: [Company type/size]",
                "persona": "Act as an HR specialist with expertise in talent acquisition and job architecture.",
                "examples": "Include responsibility statements, qualification requirements, company culture elements, and benefits highlights.",
                "output_format": "Structure as: Job Summary, Key Responsibilities, Required Qualifications, Preferred Qualifications, and Benefits.",
                "constraints": "Clear and specific requirements. Inclusive language. Realistic expectations. Competitive positioning. Legal compliance."
            },

            # === CUSTOMER SERVICE ===
            "Customer Support": {
                "instructions": "Provide exceptional customer support that resolves issues effectively while maintaining positive relationships.",
                "context": "Issue Type: [Technical/billing/product/service] Customer: [Customer profile/history] Channel: [Phone/email/chat]",
                "persona": "Act as a customer service specialist with expertise in problem resolution and relationship management.",
                "examples": "Include empathy statements, solution options, escalation procedures, and follow-up protocols.",
                "output_format": "Present as: Issue Acknowledgment, Problem Analysis, Solution Options, Resolution Steps, and Follow-up Plan.",
                "constraints": "Empathetic tone. Clear solutions. Reasonable timelines. Escalation path. Customer satisfaction focus."
            },
            "FAQ Creation": {
                "instructions": "Create comprehensive frequently asked questions that address common customer concerns proactively.",
                "context": "Product/Service: [What you're supporting] Common Issues: [Frequent customer questions] Audience: [Customer types]",
                "persona": "Act as a customer experience specialist with expertise in self-service content and customer journey optimization.",
                "examples": "Include clear questions, step-by-step answers, troubleshooting guides, and escalation information.",
                "output_format": "Structure as: Question Categories, Clear Answers, Step-by-step Instructions, Related Resources, and Contact Information.",
                "constraints": "Customer-friendly language. Comprehensive coverage. Easy navigation. Regular updates. Mobile-friendly format."
            },
            "User Manual": {
                "instructions": "Write a comprehensive user manual that helps customers effectively use your product or service.",
                "context": "Product: [Product name/type] Users: [User skill level] Features: [Key features to cover]",
                "persona": "Act as a technical writer with expertise in user documentation and customer education.",
                "examples": "Include setup instructions, feature explanations, troubleshooting guides, and best practices.",
                "output_format": "Present as: Getting Started, Feature Guide, Troubleshooting, Best Practices, and Support Resources.",
                "constraints": "Clear instructions. Visual aids. Progressive complexity. Searchable format. Regular updates based on user feedback."
            },

            # === SALES & MARKETING ===
            "Sales Proposal": {
                "instructions": "Create a compelling sales proposal that demonstrates value and persuades prospects to make a purchase decision.",
                "context": "Client: [Client name/industry] Solution: [Product/service offered] Competition: [Competitive landscape]",
                "persona": "Act as a sales professional with expertise in consultative selling and proposal writing.",
                "examples": "Include needs analysis, solution benefits, pricing strategy, and success stories from similar clients.",
                "output_format": "Structure as: Executive Summary, Needs Analysis, Proposed Solution, Investment/Pricing, Implementation Timeline, and Next Steps.",
                "constraints": "Client-specific customization. Clear value proposition. Competitive differentiation. Realistic timelines. Professional presentation."
            },
            "Marketing Strategy": {
                "instructions": "Develop a comprehensive marketing strategy that drives brand awareness, engagement, and conversions.",
                "context": "Company: [Company/product] Market: [Target market] Goals: [Marketing objectives] Budget: [Budget considerations]",
                "persona": "Act as a marketing strategist with expertise in integrated marketing communications and growth strategies.",
                "examples": "Include market segmentation, channel strategy, content planning, and campaign examples.",
                "output_format": "Present as: Market Analysis, Target Segments, Marketing Mix, Channel Strategy, Budget Allocation, and Success Metrics.",
                "constraints": "Data-driven decisions. Integrated approach. Measurable objectives. Budget optimization. Competitive advantage focus."
            },
            "Product Launch": {
                "instructions": "Plan a comprehensive product launch strategy that maximizes market impact and adoption.",
                "context": "Product: [Product description] Market: [Target market] Timeline: [Launch timeline] Resources: [Available resources]",
                "persona": "Act as a product marketing manager with expertise in go-to-market strategies and launch execution.",
                "examples": "Include pre-launch activities, launch day tactics, post-launch optimization, and success metrics.",
                "output_format": "Structure as: Launch Strategy, Pre-launch Activities, Launch Execution, Marketing Channels, and Success Measurement.",
                "constraints": "Coordinated timeline. Multi-channel approach. Risk mitigation. Success metrics. Post-launch optimization plan."
            },

            # === PROBLEM SOLVING ===
            "Problem Solving": {
                "instructions": "Analyze the problem and provide a comprehensive solution with step-by-step implementation guidance.",
                "context": "Problem: [Describe the problem] Background: [Provide relevant context] Stakeholders: [Who is affected]",
                "persona": "Act as an experienced consultant specializing in problem-solving and strategic planning.",
                "examples": "Similar solutions should include root cause analysis, multiple solution options, and implementation steps.",
                "output_format": "Structure as: Problem Analysis, Root Cause Analysis, Solution Options, Recommended Approach, Implementation Steps, and Success Metrics.",
                "constraints": "Focus on practical, actionable solutions. Consider resource constraints and timeline. Be specific and measurable."
            },
            "Decision Making": {
                "instructions": "Provide a structured decision-making framework that evaluates options and recommends the best course of action.",
                "context": "Decision: [Decision to be made] Options: [Available alternatives] Criteria: [Decision criteria] Timeline: [Decision timeline]",
                "persona": "Act as a decision analysis expert with expertise in structured decision-making and risk assessment.",
                "examples": "Include decision matrices, risk analysis, cost-benefit comparisons, and implementation considerations.",
                "output_format": "Present as: Decision Context, Option Analysis, Risk Assessment, Cost-Benefit Analysis, and Recommendation.",
                "constraints": "Objective evaluation criteria. Risk considerations. Implementation feasibility. Clear rationale. Contingency planning."
            },
            "Process Improvement": {
                "instructions": "Analyze current processes and recommend improvements that increase efficiency and effectiveness.",
                "context": "Process: [Process to improve] Current State: [How it works now] Problems: [Issues identified] Goals: [Improvement objectives]",
                "persona": "Act as a process improvement specialist with expertise in lean methodologies and operational excellence.",
                "examples": "Include current state analysis, inefficiency identification, improvement recommendations, and implementation roadmap.",
                "output_format": "Structure as: Current State Analysis, Problem Identification, Improvement Recommendations, Implementation Plan, and Success Metrics.",
                "constraints": "Measurable improvements. Change management considerations. Resource requirements. Timeline planning. Continuous improvement mindset."
            },

            # === CODE REVIEW & DEVELOPMENT ===
            "Code Review": {
                "instructions": "Review the provided code and give constructive feedback on quality, performance, security, and best practices.",
                "context": "Code: [Paste your code here] Language: [Specify programming language] Purpose: [Describe what the code does]",
                "persona": "Act as a senior software developer with expertise in code quality, security, and best practices.",
                "examples": "Similar reviews should cover: code structure, performance optimization, security considerations, and maintainability.",
                "output_format": "Structure as: Overview, Strengths, Issues Found, Specific Recommendations, and Code Examples. Use clear headings.",
                "constraints": "Focus on constructive feedback. Provide specific examples and alternatives. Consider maintainability and scalability."
            },
            "Architecture Review": {
                "instructions": "Review the system architecture and provide recommendations for scalability, maintainability, and best practices.",
                "context": "System: [System description] Architecture: [Current architecture] Requirements: [Performance/scalability requirements]",
                "persona": "Act as a software architect with expertise in system design and scalable architecture patterns.",
                "examples": "Include architecture diagrams, scalability analysis, security considerations, and technology recommendations.",
                "output_format": "Present as: Architecture Overview, Scalability Analysis, Security Review, Technology Recommendations, and Implementation Roadmap.",
                "constraints": "Focus on long-term maintainability. Consider performance implications. Security best practices. Technology evolution. Team capabilities."
            },
            "Database Design": {
                "instructions": "Design an efficient database schema that supports application requirements and performance needs.",
                "context": "Application: [Application type] Data: [Data types/volumes] Requirements: [Performance/scalability needs]",
                "persona": "Act as a database architect with expertise in data modeling and performance optimization.",
                "examples": "Include entity-relationship diagrams, indexing strategies, normalization considerations, and query optimization.",
                "output_format": "Structure as: Data Model, Schema Design, Indexing Strategy, Performance Considerations, and Maintenance Guidelines.",
                "constraints": "Normalize appropriately. Performance optimization. Data integrity. Scalability planning. Backup and recovery considerations."
            }
        }

        # Organize templates by category for better user experience
        categories = {
            "BUSINESS & STRATEGY": [
                "Business Plan", "Market Research", "Brand Strategy", "SWOT Analysis"
            ],
            "CONTENT & MARKETING": [
                "Blog Post", "Social Media Campaign", "Email Marketing", "SEO Content"
            ],
            "EDUCATION & TRAINING": [
                "Course Curriculum", "Training Manual", "Tutorial Guide", "Assessment Design"
            ],
            "TECHNICAL & DEVELOPMENT": [
                "API Documentation", "Code Documentation", "Technical Specification", "Bug Report"
            ],
            "RESEARCH & ANALYSIS": [
                "Research Paper", "Literature Review", "Data Analysis", "Survey Design"
            ],
            "CREATIVE & DESIGN": [
                "Creative Brief", "UX Design", "Video Script", "Copywriting"
            ],
            "PROFESSIONAL & CAREER": [
                "Resume", "Cover Letter", "Performance Review", "Job Description"
            ],
            "CUSTOMER SERVICE": [
                "Customer Support", "FAQ Creation", "User Manual"
            ],
            "SALES & MARKETING": [
                "Sales Proposal", "Marketing Strategy", "Product Launch"
            ],
            "PROBLEM SOLVING": [
                "Problem Solving", "Decision Making", "Process Improvement"
            ],
            "CODE REVIEW & DEVELOPMENT": [
                "Code Review", "Architecture Review", "Database Design"
            ]
        }

        # Create a flattened list with category headers
        template_options = []
        for category, template_names in categories.items():
            template_options.append(f"─── {category} ───")
            template_options.extend(template_names)
            template_options.append("")  # Add spacing between categories

        # Remove the last empty item
        if template_options and template_options[-1] == "":
            template_options.pop()

        template_choice, ok = QInputDialog.getItem(
            self, "Load Template", "Choose a template category and template:", template_options, 0, False
        )

        if ok and template_choice:
            # Skip category headers and empty lines
            if template_choice.startswith("───") or template_choice == "":
                create_themed_message_box(
                    self, "Invalid Selection",
                    "Please select a template, not a category header.",
                    "info",
                    self.dark_theme
                ).exec()
                return

            # Load the selected template
            if template_choice in templates:
                template = templates[template_choice]
                for section_key, content in template.items():
                    if section_key in self.section_widgets:
                        self.section_widgets[section_key].setPlainText(content)
                self.update_preview()
            else:
                create_themed_message_box(
                    self, "Template Not Found",
                    f"Template '{template_choice}' not found in the template library.",
                    "error",
                    self.dark_theme
                ).exec()

    def copy_prompt(self):
        """Copy the generated prompt to clipboard"""
        prompt = self.preview_text.toPlainText()
        if prompt and prompt != "Fill out the sections above to see your prompt preview...":
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(prompt)

                create_themed_message_box(
                    self, "Copied!",
                    "Prompt copied to clipboard successfully.",
                    "success",
                    self.dark_theme
                ).exec()
            else:
                create_themed_message_box(
                    self, "Error",
                    "Failed to access clipboard.",
                    "error",
                    self.dark_theme
                ).exec()
        else:
            create_themed_message_box(
                self, "Nothing to Copy",
                "Please fill out the sections to generate a prompt first.",
                "info",
                self.dark_theme
            ).exec()

    def use_prompt(self):
        """Use the generated prompt"""
        prompt = self.preview_text.toPlainText()
        if prompt and prompt != "Fill out the sections above to see your prompt preview...":
            self.template_selected.emit(prompt)
            self.accept()
        else:
            create_themed_message_box(
                self, "Incomplete Prompt",
                "Please fill out at least some sections to create a prompt.",
                "warning",
                self.dark_theme
            ).exec()

    def apply_theme_styles(self):
        """Apply theme-aware styling to the dialog"""
        dialog_styles = get_dialog_theme_styles(self.dark_theme)

        # Apply dialog-wide styles
        self.setStyleSheet(dialog_styles + """
            QLabel#title_label {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 5px;
            }

            QLabel#description_label {
                margin-bottom: 15px;
                font-size: 13px;
                padding: 5px;
            }

            QGroupBox#framework_group {
                font-weight: bold;
                margin: 10px 0;
                padding-top: 15px;
            }

            QGroupBox#preview_group {
                font-weight: bold;
                margin: 10px 0;
                padding-top: 15px;
            }

            QLabel#section_description {
                font-size: 12px;
                margin-bottom: 8px;
                font-style: italic;
            }

            QTextEdit#section_input {
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                line-height: 1.4;
            }

            QTextEdit#preview_text {
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                line-height: 1.4;
            }

            QPushButton#examples_button {
                padding: 4px 8px;
                font-size: 11px;
                border-radius: 3px;
                margin-bottom: 5px;
            }

            QPushButton#clear_button, QPushButton#template_button,
            QPushButton#copy_button, QPushButton#use_button,
            QPushButton#cancel_button {
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 100px;
            }

            QScrollArea {
                border: none;
                border-radius: 5px;
            }
        """)

    def generate_missing_sections(self):
        """Generate content for empty sections based on filled sections"""
        if not self.multi_client:
            create_themed_message_box(
                self, "Feature Unavailable",
                "AI generation is not available. Please ensure API settings are configured.",
                "warning",
                self.dark_theme
            ).exec()
            return

        try:
            # Analyze which sections are filled and which are empty
            filled_sections = {}
            empty_sections = {}

            for section_key, section_info in self.framework_sections.items():
                if section_key in self.section_widgets:
                    text_widget = self.section_widgets[section_key]
                    content = text_widget.toPlainText().strip()

                    if content:
                        filled_sections[section_key] = {
                            'title': section_info['title'],
                            'content': content
                        }
                    else:
                        empty_sections[section_key] = section_info

            if not filled_sections:
                create_themed_message_box(
                    self, "No Content to Analyze",
                    "Please fill out at least one section before generating missing content.",
                    "info",
                    self.dark_theme
                ).exec()
                return

            if not empty_sections:
                create_themed_message_box(
                    self, "No Missing Sections",
                    "All sections are already filled out!",
                    "info",
                    self.dark_theme
                ).exec()
                return

            # Show progress indication
            generate_btn = self.findChild(QPushButton, "generate_button")
            if generate_btn:
                generate_btn.setText("🔄 Generating...")
                generate_btn.setEnabled(False)

            # Create the generation prompt
            generation_prompt = self.create_generation_prompt(filled_sections, empty_sections)

            # Make API call to generate content
            self.call_api_for_generation(generation_prompt, empty_sections, generate_btn)

        except Exception as e:
            create_themed_message_box(
                self, "Generation Error",
                f"Failed to generate missing sections: {str(e)}",
                "error",
                self.dark_theme
            ).exec()

            # Reset button state
            generate_btn = self.findChild(QPushButton, "generate_button")
            if generate_btn:
                generate_btn.setText("🪄 Generate Missing Sections")
                generate_btn.setEnabled(True)

    def create_generation_prompt(self, filled_sections, empty_sections):
        """Create a prompt for generating missing sections"""
        prompt_parts = [
            "You are an expert at creating comprehensive AI prompts. I have partially filled out a prompt framework and need you to generate content for the missing sections.",
            "",
            "## Filled Sections:",
        ]

        for section_key, section_data in filled_sections.items():
            prompt_parts.append(f"### {section_data['title']}")
            prompt_parts.append(section_data['content'])
            prompt_parts.append("")

        prompt_parts.append("## Missing Sections to Generate:")
        for section_key, section_info in empty_sections.items():
            prompt_parts.append(f"### {section_info['title']}")
            prompt_parts.append(f"Description: {section_info['description']}")
            prompt_parts.append(f"Examples: {', '.join(section_info['examples'][:2])}")
            prompt_parts.append("")

        prompt_parts.extend([
            "## Instructions:",
            "1. Analyze the filled sections to understand the user's intent and narrative",
            "2. Generate appropriate content for each missing section that fits cohesively with the filled sections",
            "3. Ensure the generated content maintains consistency in tone, scope, and purpose",
            "4. Make the content specific and actionable, not generic",
            "5. Return ONLY the generated content for each missing section in this exact format:",
            "",
            "```",
            "SECTION_KEY: content_here",
            "```",
            "",
            "Do not include any explanations or additional text outside the specified format."
        ])

        return "\n".join(prompt_parts)

    def call_api_for_generation(self, generation_prompt, empty_sections, generate_btn):
        """Make API call to generate content asynchronously"""
        if not self.multi_client:
            create_themed_message_box(
                self, "API Error",
                "API client is not available.",
                "error",
                self.dark_theme
            ).exec()
            return

        try:
            # Get the current provider and model
            current_provider = getattr(self.multi_client, 'current_provider', 'openai')
            current_model = getattr(self.multi_client, 'current_model', 'gpt-3.5-turbo')

            # Create a simple request
            if hasattr(self.multi_client, 'send_message'):
                response = self.multi_client.send_message(
                    generation_prompt,
                    provider=current_provider,
                    model=current_model,
                    temperature=0.7,
                    max_tokens=2000
                )
            else:
                # Fallback if send_message doesn't exist
                create_themed_message_box(
                    self, "API Error",
                    "API client send_message method not available.",
                    "error",
                    self.dark_theme
                ).exec()
                return

            if response and response.get('content'):
                self.parse_and_fill_generated_content(response['content'], empty_sections)
            else:
                create_themed_message_box(
                    self, "Generation Failed",
                    "Failed to generate content. Please try again.",
                    "error",
                    self.dark_theme
                ).exec()

        except Exception as e:
            create_themed_message_box(
                self, "API Error",
                f"Error calling API: {str(e)}",
                "error",
                self.dark_theme
            ).exec()
        finally:
            # Reset button state
            if generate_btn:
                generate_btn.setText("🪄 Generate Missing Sections")
                generate_btn.setEnabled(True)

    def parse_and_fill_generated_content(self, generated_content, empty_sections):
        """Parse the generated content and fill the empty sections"""
        try:
            # Extract sections from the generated content
            sections_filled = 0
            lines = generated_content.split('\n')
            current_section = None
            current_content = []

            for line in lines:
                line = line.strip()
                if ':' in line and line.split(':')[0].lower() in [key.lower() for key in empty_sections.keys()]:
                    # Save previous section if exists
                    if current_section and current_content:
                        content_text = '\n'.join(current_content).strip()
                        if content_text and current_section in self.section_widgets:
                            self.section_widgets[current_section].setPlainText(content_text)
                            sections_filled += 1

                    # Start new section
                    parts = line.split(':', 1)
                    section_key = parts[0].strip().lower()

                    # Find matching section key
                    current_section = None
                    for key in empty_sections.keys():
                        if key.lower() == section_key:
                            current_section = key
                            break

                    current_content = []
                    if len(parts) > 1:
                        current_content.append(parts[1].strip())

                elif current_section and line:
                    current_content.append(line)

            # Handle last section
            if current_section and current_content:
                content_text = '\n'.join(current_content).strip()
                if content_text and current_section in self.section_widgets:
                    self.section_widgets[current_section].setPlainText(content_text)
                    sections_filled += 1

            # Update preview
            self.update_preview()

            # Show success message
            if sections_filled > 0:
                create_themed_message_box(
                    self, "Generation Complete",
                    f"Successfully generated content for {sections_filled} section(s).",
                    "success",
                    self.dark_theme
                ).exec()
            else:
                create_themed_message_box(
                    self, "Generation Issues",
                    "Content was generated but couldn't be parsed properly. Please review and edit manually.",
                    "warning",
                    self.dark_theme
                ).exec()

        except Exception as e:
            create_themed_message_box(
                self, "Parsing Error",
                f"Error parsing generated content: {str(e)}",
                "error",
                self.dark_theme
            ).exec()

def test_prompt_dialog():
    """Test the prompt template dialog"""
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    dialog = PromptTemplateDialog()

    def on_template_selected(template):
        print("Selected template:")
        print("=" * 50)
        print(template)
        print("=" * 50)

    dialog.template_selected.connect(on_template_selected)
    dialog.exec()

    app.quit()


if __name__ == "__main__":
    test_prompt_dialog()
