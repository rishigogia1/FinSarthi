export type Money = number;

export const currency = (n: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

export const user = {
  name: "Rishi",
  fullName: "Rishi Sharma",
  email: "rishi@finsarthi.app",
  initials: "RS",
  handle: "@rishi",
};

export const promptCards = [
  { icon: "PiggyBank", title: "Save Money", desc: "Find smart ways to save more each month", color: "success", workflowType: "save_money" },
  { icon: "Landmark", title: "Government Schemes", desc: "Discover schemes you qualify for", color: "primary", workflowType: "government_schemes" },
  { icon: "ShieldCheck", title: "Fraud Protection", desc: "Stay safe from scams and fraud", color: "warning", workflowType: "fraud_protection" },
  { icon: "Target", title: "Financial Goals", desc: "Plan and track long-term goals", color: "accent", workflowType: "financial_goals" },
  { icon: "TrendingUp", title: "Investment Advice", desc: "Get personalized investment ideas", color: "primary", workflowType: "investment_advice" },
  { icon: "BookOpen", title: "Learn Finance", desc: "Master money concepts step by step", color: "secondary", workflowType: "learn_finance" },
] as const;

export const suggestedPrompts = [
  "How can I save ₹5,000 more each month?",
  "Am I eligible for PM Kisan Yojana?",
  "Is this UPI request safe? +91 98xxx",
  "Plan a 3-year goal to buy a car",
  "Should I invest in an index fund?",
  "Explain SIP vs lump sum simply",
];

export const conversations = [
  { id: "c1", title: "Emergency fund for 6 months", updated: "2h ago", pinned: true },
  { id: "c2", title: "Best SIP under ₹5,000", updated: "Yesterday" },
  { id: "c3", title: "Health insurance for parents", updated: "2d ago" },
  { id: "c4", title: "Home loan prepayment plan", updated: "1w ago" },
  { id: "c5", title: "Tax saving under 80C", updated: "1w ago" },
  { id: "c6", title: "Fraud check — SMS from bank", updated: "2w ago" },
];

export const agents = [
  {
    id: "planner",
    name: "Planner",
    role: "Budget & Goals",
    desc: "Builds monthly plans and tracks progress toward your goals.",
    status: "Analyzing spending patterns…",
    progress: 62,
    color: "primary",
    activity: [
      "Reviewed last 30 days of transactions",
      "Draft budget: essentials 55%, savings 25%, wants 20%",
      "Flagged 3 recurring subscriptions to review",
    ],
  },
  {
    id: "coach",
    name: "Coach",
    role: "Habits & Behavior",
    desc: "Nudges better money habits without judgment.",
    status: "Reviewing habits this week…",
    progress: 40,
    color: "success",
    activity: [
      "You saved 4 out of 7 days — nice streak",
      "Suggested weekly no-spend day: Wednesday",
    ],
  },
  {
    id: "guardian",
    name: "Guardian",
    role: "Fraud & Safety",
    desc: "Watches for scams, suspicious links, and risky requests.",
    status: "Checking for fraud signals…",
    progress: 88,
    color: "warning",
    activity: [
      "Verified 12 payment requests today",
      "Blocked 1 suspicious phishing link",
    ],
  },
  {
    id: "navigator",
    name: "Navigator",
    role: "Schemes & Benefits",
    desc: "Finds government schemes and benefits you qualify for.",
    status: "Searching schemes…",
    progress: 25,
    color: "chart-5",
    activity: [
      "Matched you to 4 eligible schemes",
      "PM Kisan · Atal Pension · Ayushman Bharat",
    ],
  },
  {
    id: "learn",
    name: "Learn",
    role: "Financial Literacy",
    desc: "Explains concepts simply, in your language.",
    status: "Preparing explanation…",
    progress: 55,
    color: "accent",
    activity: [
      "Prepared 3-min primer on SIPs",
      "Bookmark: “What is a credit score?”",
    ],
  },
] as const;

export const insights = [
  { title: "Financial Health Score", value: "78 / 100", trend: "+4 this month", tone: "success" },
  { title: "Monthly Savings", value: currency(18400), trend: "+₹2,100 vs last", tone: "success" },
  { title: "Monthly Spending", value: currency(42800), trend: "-3.2%", tone: "primary" },
  { title: "Emergency Fund", value: "4.2 months", trend: "Goal: 6 months", tone: "warning" },
];

export const spendingByCategory = [
  { name: "Rent", value: 18000 },
  { name: "Food", value: 8400 },
  { name: "Transport", value: 3200 },
  { name: "Utilities", value: 2600 },
  { name: "Health", value: 1800 },
  { name: "Other", value: 8800 },
];

export const savingsTrend = [
  { m: "Feb", saved: 9200 },
  { m: "Mar", saved: 11400 },
  { m: "Apr", saved: 12800 },
  { m: "May", saved: 14100 },
  { m: "Jun", saved: 16300 },
  { m: "Jul", saved: 18400 },
];

export const goals = [
  { id: "g1", title: "Emergency Fund", target: 300000, saved: 210000, deadline: "Dec 2026", tag: "Safety" },
  { id: "g2", title: "Trip to Kerala", target: 80000, saved: 32000, deadline: "Mar 2027", tag: "Lifestyle" },
  { id: "g3", title: "MacBook for work", target: 150000, saved: 58000, deadline: "Aug 2027", tag: "Work" },
  { id: "g4", title: "Down payment", target: 800000, saved: 145000, deadline: "2029", tag: "Home" },
];

export const knowledgeTopics = [
  { title: "PM Kisan Samman Nidhi", tag: "Scheme", desc: "₹6,000/year support for eligible farmer families." },
  { title: "Atal Pension Yojana", tag: "Scheme", desc: "Guaranteed pension for unorganised sector workers." },
  { title: "How SIPs work", tag: "Investing", desc: "Systematic investment plans, explained in 3 minutes." },
  { title: "Understanding your credit score", tag: "Credit", desc: "What moves your CIBIL score up or down." },
  { title: "Term insurance basics", tag: "Insurance", desc: "How much cover you actually need." },
  { title: "Section 80C explained", tag: "Tax", desc: "The most-used tax saving section, simplified." },
  { title: "Home loan prepayment", tag: "Loans", desc: "When to prepay vs invest the surplus." },
  { title: "Spotting UPI scams", tag: "Safety", desc: "Common tricks and how to stay safe." },
];

export const chatSample: {
  role: "user" | "assistant";
  text: string;
  chart?: boolean;
  sources?: string[];
  followups?: string[];
}[] = [
  { role: "user", text: "How can I save ₹5,000 more each month without cutting things I love?" },
  {
    role: "assistant",
    text:
      "Great question. Based on your last 3 months, here's a realistic plan:\n\n" +
      "- **Subscriptions:** You have 3 overlapping OTT plans (~₹1,100/mo). Keep one.\n" +
      "- **Food delivery:** Averaging ₹4,800/mo. A 2-per-week cap saves ~₹1,800.\n" +
      "- **Auto-sweep:** Move ₹2,100 on payday into a liquid fund.\n\n" +
      "That's ₹5,000 without touching travel or gifts.",
    chart: true,
    sources: ["Your transactions · Jun–Aug", "RBI: Household savings", "FinSarthi Coach"],
    followups: [
      "Set up the auto-sweep",
      "Which subscription should I keep?",
      "Show my food delivery trend",
    ],
  },
];
