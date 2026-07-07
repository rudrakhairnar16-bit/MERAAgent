from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica","I",8)
            self.set_text_color(150,150,150)
            self.cell(0,10,"Agents of SigNoz 2026 | Team Enthusiast | KPGU Vadodara",align="R")
            self.ln(12)
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica","I",8)
        self.set_text_color(150,150,150)
        self.cell(0,10,f"Page {self.page_no()}/{{nb}}",align="C")
    def stitle(self,t):
        self.set_font("Helvetica","B",14)
        self.set_text_color(20,60,120)
        self.cell(0,12,t,new_x="LMARGIN",new_y="NEXT")
        self.set_draw_color(20,60,120)
        self.line(10,self.get_y(),200,self.get_y())
        self.ln(4)
    def ssub(self,t):
        self.set_font("Helvetica","B",11)
        self.set_text_color(40,40,40)
        self.cell(0,8,t,new_x="LMARGIN",new_y="NEXT")
        self.ln(1)
    def body(self,t):
        self.set_font("Helvetica","",10)
        self.set_text_color(30,30,30)
        self.multi_cell(0,6,t)
        self.ln(2)
    def bul(self,t):
        self.set_font("Helvetica","",10)
        self.set_text_color(30,30,30)
        self.cell(8,6,"-")
        self.multi_cell(0,6,t)
        self.ln(1)
    def kv(self,k,v):
        self.set_font("Helvetica","B",10)
        w=self.get_string_width(k)+4
        self.cell(w,6,k)
        self.set_font("Helvetica","",10)
        self.multi_cell(0,6,v)
        self.ln(1)

pdf=PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True,margin=20)

# COVER
pdf.add_page()
pdf.ln(40)
pdf.set_font("Helvetica","B",28)
pdf.set_text_color(20,60,120)
pdf.cell(0,14,"MERA",align="C",new_x="LMARGIN",new_y="NEXT")
pdf.set_font("Helvetica","",16)
pdf.set_text_color(60,60,60)
pdf.cell(0,10,"Mirror Entity Recursive Agent",align="C",new_x="LMARGIN",new_y="NEXT")
pdf.ln(6)
pdf.set_font("Helvetica","I",12)
pdf.set_text_color(100,100,100)
pdf.cell(0,8,"Self-Healing AI Agent Powered by SigNoz Observability",align="C",new_x="LMARGIN",new_y="NEXT")
pdf.ln(20)
pdf.set_draw_color(20,60,120)
pdf.line(60,pdf.get_y(),150,pdf.get_y())
pdf.ln(10)
pdf.set_font("Helvetica","",11)
pdf.set_text_color(40,40,40)
pdf.cell(0,7,"Track 03 - Build Your Own",align="C",new_x="LMARGIN",new_y="NEXT")
pdf.cell(0,7,"Agents of SigNoz Hackathon 2026 | SigNoz x WeMakeDevs",align="C",new_x="LMARGIN",new_y="NEXT")
pdf.ln(4)
pdf.cell(0,7,"Team Enthusiast",align="C",new_x="LMARGIN",new_y="NEXT")
pdf.cell(0,7,"Dr. Kiran & Pallavi Patel Global University (KPGU), Vadodara",align="C",new_x="LMARGIN",new_y="NEXT")
pdf.ln(10)
pdf.cell(0,7,f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}",align="C",new_x="LMARGIN",new_y="NEXT")

# WHAT
pdf.add_page()
pdf.stitle("1. Kya? (What is MERA?)")
pdf.body("MERA ek self-healing AI agent system hai jo apne aap ko observe karta hai, mistakes detect karta hai, aur khud ko fix karta hai - without human intervention.")
pdf.ssub("Core Concept")
pdf.body("Recursive observability loop: Main Agent works with OTel, Mirror Agent reads traces via SigNoz MCP, detects anomalies, generates fixes. Everything visualized on SigNoz dashboards with alerts.")
pdf.ssub("Components")
pdf.bul("Main Agent (PR Reviewer): Llama 3.2 (local) code review, OTel-instrumented")
pdf.bul("Mirror Agent (Observer/Healer): MCP queries, anomaly detection, fix generation")
pdf.bul("SigNoz Platform: All 6 features - Traces, Metrics, Logs, Dashboards, Alerts, MCP")
pdf.bul("Self-Healing Loop: Work -> Watch -> Detect -> Fix -> Update")

# WHY
pdf.add_page()
pdf.stitle("2. Kyu? (Why MERA?)")
pdf.ssub("The Problem")
pdf.body("AI agents are black boxes. LLM hallucinations, latency spikes, cost explosions - all invisible. Traditional tools show what broke but not why or how to fix.")
pdf.ssub("Pain Points")
pdf.bul("AI agents chain LLM calls, tools, vector DBs autonomously - all opaque")
pdf.bul("Latency, cost, hallucination issues invisible until users complain")
pdf.bul("Fragmented observability (different tools for logs/metrics/traces)")
pdf.bul("No automated self-healing - manual debugging every time")
pdf.ssub("Why SigNoz?")
pdf.body("OpenTelemetry-native (agents understand OTel), one platform for all signals, MCP server for programmatic access, open source (no lock-in), consistent schema across traces/metrics/logs.")
pdf.ssub("Mission")
pdf.body('"If you cannot observe your AI agents, you do not own them." MERA proves AI systems can be self-aware, self-debugging, and self-healing with proper observability.')

# HOW
pdf.add_page()
pdf.stitle("3. Kese? (How is it built?)")
pdf.body("Three layers: Agent Layer (Main + Mirror), Observability Layer (SigNoz + OTel Collector), Infrastructure Layer (Docker + Foundry).")
pdf.ssub("Tech Stack")
pdf.kv("Language:","Python 3.11+")
pdf.kv("AI/LLM:","Ollama + Llama 3.2 3B (local, free, no API key)")
pdf.kv("Observability:","OpenTelemetry SDK + OTLP HTTP Exporter")
pdf.kv("SigNoz:","Traces + Metrics + Logs + Dashboards + Alerts + MCP")
pdf.kv("Deployment:","Docker + SigNoz Foundry (casting.yaml)")
pdf.ssub("Main Agent (agent.py)")
pdf.bul("Ollama OpenAI-compatible API se PR review agent with OTel spans")
pdf.bul("Custom attributes: code.language, review.confidence_score, review.issues_count, llm.latency_ms")
pdf.bul("Anomaly score from recent history (avg confidence, issue count)")
pdf.bul("Robust JSON parsing with regex fallback for LLM output")
pdf.ssub("Mirror Agent (mirror.py)")
pdf.bul("SigNoz MCP se traces/alerts fetch via JSON-RPC")
pdf.bul("3 anomaly rules: high latency (>5s), low confidence (<0.5), zero-issues-suspicious")
pdf.bul("LLM-based fix suggestion generation per anomaly")
pdf.bul("Auto-creates SigNoz dashboards + alert rules via MCP API")
pdf.bul("Self-OTel-instrumented (meta-recursive)")
pdf.ssub("Orchestrator (run.py)")
pdf.bul("Main agent continuous loop (3 sample codes cycling)")
pdf.bul("Mirror agent 3 self-healing cycles with 8s intervals")
pdf.bul("Threading for concurrent execution")

# WHEN
pdf.add_page()
pdf.stitle("4. Kab? (Timeline)")
pdf.kv("Hackathon:","July 20 - July 26, 2026")
pdf.kv("Registration:","https://forms.gle/uxaLXAXmtKwz8uYh9")
pdf.ln(2)
days=[
("Pre-Hackathon","Ollama install, SigNoz Foundry setup, OTel learn"),
("Day 1 (Jul 20)","Main Agent code + OTel instrumentation + test"),
("Day 2 (Jul 21)","Mirror Agent + MCP integration + anomaly detection"),
("Day 3 (Jul 22)","Self-healing logic + fix generation + orchestration"),
("Day 4 (Jul 23)","Dashboards + Alerts + Docker + Foundry deploy"),
("Day 5 (Jul 24)","Tests + README + architecture diagram + blog"),
("Day 6 (Jul 25)","Demo video (2 min) + submit + social media"),
("Day 7 (Jul 26)","Buffer / Judge Q&A prep")
]
for d,t in days:
    pdf.set_font("Helvetica","B",10)
    pdf.set_text_color(20,60,120)
    pdf.cell(0,7,d,new_x="LMARGIN",new_y="NEXT")
    pdf.bul(t)

# TOOLS
pdf.add_page()
pdf.stitle("5. Tools Used & Free Status")
tools=[
("Ollama","MIT","Fully Free","Local LLM, no API key needed"),
("Llama 3.2 3B","Meta OSS","Fully Free","2GB model, runs locally"),
("SigNoz (Self-Host)","MIT","Fully Free","Local Docker deploy"),
("OpenTelemetry SDK","Apache 2.0","Fully Free","CNCF standard"),
("Python 3.11+","PSF","Fully Free","Language runtime"),
("Docker","Freemium","Free personal","Desktop free tier"),
("Foundry CLI","Open Source","Fully Free","npm package"),
("GitHub","Freemium","Free unlimited","Public repos"),
("AWS Credits","Sponsored","$100/participant","Builder Center signup"),
("pytest","MIT","Fully Free","Testing"),
("fpdf2 (Report)","LGPL","Fully Free","PDF generation")
]
pdf.set_font("Helvetica","B",9)
pdf.set_fill_color(20,60,120)
pdf.set_text_color(255,255,255)
cw=[50,40,30,65]
pdf.cell(cw[0],8,"Tool",border=1,fill=True,align="C")
pdf.cell(cw[1],8,"License",border=1,fill=True,align="C")
pdf.cell(cw[2],8,"Free?",border=1,fill=True,align="C")
pdf.cell(cw[3],8,"Notes",border=1,fill=True,align="C")
pdf.ln()
pdf.set_font("Helvetica","",8)
pdf.set_text_color(30,30,30)
for r in tools:
    for i,c in enumerate(r):
        pdf.cell(cw[i],7,c,border=1,align="C" if i==2 else "L")
    pdf.ln()
pdf.ln(5)
pdf.body("Cost estimate: $0. Zero. Ollama local hai, SigNoz self-host free hai, AWS $100 free credits mil rahe hain. Ek bhi paisa nahi lagana padega.")

# SCORE
pdf.add_page()
pdf.stitle("6. Judging Score Card")
scoring=[
("Potential Impact","20%","18/20","Self-debugging AI = trillion-dollar problem. -2 for use-case scope."),
("Creativity","20%","20/20","Recursive self-watching agent never done in hackathon. Maximum."),
("Technical Excellence","20%","15/20","OTel+MCP+LLM clean. -5 for edge cases (agent corruption)."),
("Best Use of SigNoz","20%","20/20","All 6 features: Traces+Metrics+Logs+Dashboards+Alerts+MCP. Max."),
("User Experience","10%","14/20","Auto-dashboards help. -6 because concept complex for non-tech judges."),
("Presentation","10%","17/20","Strong docs+diagram+tests+script. -3 for production polish.")
]
pdf.set_font("Helvetica","B",9)
pdf.set_fill_color(20,60,120)
pdf.set_text_color(255,255,255)
cw=[38,14,14,119]
pdf.cell(cw[0],8,"Criteria",border=1,fill=True,align="C")
pdf.cell(cw[1],8,"Wt",border=1,fill=True,align="C")
pdf.cell(cw[2],8,"Score",border=1,fill=True,align="C")
pdf.cell(cw[3],8,"Explanation",border=1,fill=True,align="C")
pdf.ln()
pdf.set_font("Helvetica","",8)
pdf.set_text_color(30,30,30)
for n,w,s,e in scoring:
    y=pdf.get_y()
    pdf.cell(cw[0],10,n,border=1)
    pdf.cell(cw[1],10,w,border=1,align="C")
    pdf.cell(cw[2],10,s,border=1,align="C")
    pdf.set_xy(10+cw[0]+cw[1]+cw[2],y)
    pdf.multi_cell(cw[3],5,e,border=1)
pdf.ln(5)
pdf.set_draw_color(20,60,120)
pdf.set_fill_color(230,240,255)
pdf.rect(10,pdf.get_y(),190,30,style="DF")
y=pdf.get_y()
pdf.set_xy(15,y+3)
pdf.set_font("Helvetica","B",16)
pdf.set_text_color(20,60,120)
pdf.cell(0,10,"Final Estimated Score: 84 / 100")
pdf.set_xy(15,y+16)
pdf.set_font("Helvetica","",10)
pdf.set_text_color(40,40,40)
pdf.cell(0,8,"Top 3 almost certain | Win probability: 70% | iPhone 17 Pro Max dono ko")

# WIN
pdf.add_page()
pdf.stitle("7. What Makes Team Enthusiast Win")
pdf.ssub("Unfair Advantages")
pdf.bul("6/6 SigNoz features used - most teams use 2-3 max")
pdf.bul("Recursive self-watching concept - extremely novel")
pdf.bul("Full OTel instrumentation - every step traced")
pdf.bul("Maximum MCP use - agents talk to observability data programmatically")
pdf.bul("Foundry deploy - casting.yaml makes it reproducible (rules requirement)")
pdf.bul("Team of 2 = focused execution, no coordination overhead")
pdf.bul("Zero cost - Ollama local LLM, no API key needed")
pdf.bul("Auto-generated dashboards + alerts impress judges")
pdf.ssub("Prize Breakdown per Member")
pdf.bul("Apple iPhone 17 Pro Max (or cash equivalent) - Track 3 winner")
pdf.bul("AWS credits: $5K (1st) / $3K (2nd) / $2K (3rd)")
pdf.bul("Job interviews at SigNoz")
pdf.bul("LEGO Ferrari SF-24 (best blog side track)")
pdf.bul("Exclusive swag (social media top 10)")
pdf.ln(10)
pdf.set_font("Helvetica","B",12)
pdf.set_text_color(20,120,60)
pdf.cell(0,10,"Strong Concept + Deep SigNoz + Clean Code + Great Demo = iPhone 17 Pro Max")
pdf.ln(20)
pdf.set_font("Helvetica","I",10)
pdf.set_text_color(100,100,100)
pdf.cell(0,6,'"If you cannot observe your AI agents, you do not own them."',align="C",new_x="LMARGIN",new_y="NEXT")
pdf.ln(4)
pdf.cell(0,6,"Team Enthusiast | Dr. Kiran & Pallavi Patel Global University, Vadodara",align="C",new_x="LMARGIN",new_y="NEXT")

pdf.output("C:\\Users\\Rudra\\Desktop\\Signoz_Agent\\Track_3\\MERA_Report.pdf")
print(f"PDF generated: {pdf.page_no()} pages")
