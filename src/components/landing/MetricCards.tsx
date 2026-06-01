import { TrendingUp, TrendingDown, AlertCircle, CheckCircle2, FileText, Target } from 'lucide-react'

export function CashflowSignalCard() {
  return (
    <div className="p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-600">Cashflow Signal</span>
        <TrendingUp className="w-4 h-4 text-emerald-500" />
      </div>
      <div className="space-y-1">
        <div className="text-2xl font-bold text-emerald-600">Stable</div>
        <div className="text-xs text-slate-500">with receivables pressure</div>
      </div>
      <div className="h-12 flex items-end space-x-1">
        {[40, 45, 42, 48, 52, 55, 58, 62, 60, 65, 68, 70].map((height, i) => (
          <div
            key={i}
            className="flex-1 bg-gradient-to-t from-emerald-400 to-emerald-300 rounded-sm"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  )
}

export function CreditReadinessCard() {
  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-600">Credit Readiness</span>
        <TrendingUp className="w-4 h-4 text-cyan-500" />
      </div>
      <div className="text-2xl font-bold text-cyan-600">Strengthening</div>
      <div className="relative w-24 h-24 mx-auto">
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="#e2e8f0"
            strokeWidth="8"
            fill="none"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="#0ea5e9"
            strokeWidth="8"
            fill="none"
            strokeDasharray={`${2 * Math.PI * 40 * 0.72} ${2 * Math.PI * 40}`}
            className="transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-slate-800">72%</span>
        </div>
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Capacity</span>
          <CheckCircle2 className="w-3 h-3 text-emerald-500" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Documentation</span>
          <CheckCircle2 className="w-3 h-3 text-emerald-500" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Repayment ability</span>
          <CheckCircle2 className="w-3 h-3 text-emerald-500" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Risk positioning</span>
          <AlertCircle className="w-3 h-3 text-amber-500" />
        </div>
      </div>
    </div>
  )
}

export function ReceivablesPressureCard() {
  return (
    <div className="p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-600">Receivables Pressure</span>
        <TrendingDown className="w-4 h-4 text-amber-500" />
      </div>
      <div className="text-2xl font-bold text-amber-600">Elevated</div>
      <div className="text-xs text-slate-500 mb-3">45-day collection period</div>
      <div className="h-16 flex items-end justify-between">
        {[45, 52, 58, 65, 72, 78, 85, 88].map((height, i) => (
          <div
            key={i}
            className="w-6 bg-gradient-to-t from-amber-400 to-amber-300 rounded-t"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  )
}

export function AdvisorActionCard() {
  return (
    <div className="p-4 space-y-2">
      <div className="flex items-center space-x-2 mb-3">
        <div className="w-8 h-8 rounded-full bg-cyan-100 flex items-center justify-center">
          <Target className="w-4 h-4 text-cyan-600" />
        </div>
        <span className="text-sm font-semibold text-slate-800">Advisor Action</span>
      </div>
      <div className="text-xs text-slate-700 font-medium">
        Prioritize collections before adding new debt.
      </div>
      <button className="text-xs text-cyan-600 font-medium hover:text-cyan-700 flex items-center space-x-1">
        <span>View Action Plan</span>
        <TrendingUp className="w-3 h-3" />
      </button>
    </div>
  )
}

export function SourceTrailCard() {
  return (
    <div className="p-3 space-y-2">
      <div className="text-xs font-medium text-slate-600 mb-2">Source Trail</div>
      <div className="flex items-center space-x-2">
        <FileText className="w-4 h-4 text-slate-400" />
        <div className="flex-1">
          <div className="text-xs font-medium text-slate-700">AR Records</div>
        </div>
      </div>
      <div className="flex items-center space-x-2 pl-6">
        <div className="w-px h-4 bg-slate-300" />
        <div className="text-xs text-slate-500">Assumptions</div>
      </div>
      <div className="flex items-center space-x-2 pl-6">
        <div className="w-px h-4 bg-slate-300" />
        <div className="text-xs text-slate-500">Signal</div>
      </div>
      <div className="flex items-center space-x-2 pl-6">
        <div className="w-px h-4 bg-slate-300" />
        <div className="text-xs text-slate-500">Recommendation</div>
      </div>
    </div>
  )
}

export function KeyAssumptionsCard() {
  return (
    <div className="p-3 space-y-2">
      <div className="text-xs font-medium text-slate-600 mb-2">Key Assumptions</div>
      <div className="space-y-2 text-xs">
        <div className="flex items-start space-x-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5" />
          <div>
            <div className="font-medium text-slate-700">Revenue growth</div>
            <div className="text-slate-500">15% YoY</div>
          </div>
        </div>
        <div className="flex items-start space-x-2">
          <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5" />
          <div>
            <div className="font-medium text-slate-700">DSO service coverage</div>
            <div className="text-slate-500">1.8x</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function FundingReadinessCard() {
  return (
    <div className="p-4 space-y-2">
      <div className="text-xs font-medium text-slate-600">Funding Readiness</div>
      <div className="text-3xl font-bold text-emerald-600">65%</div>
      <div className="space-y-1.5">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-xs text-slate-600">Documentation gap detected</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-amber-500" />
          <span className="text-xs text-slate-600">Next action: Improve collections visibility</span>
        </div>
      </div>
    </div>
  )
}

export function FinancialRecordsSidebar() {
  const records = [
    { icon: FileText, label: 'Bank Exports', color: 'text-blue-600' },
    { icon: FileText, label: 'Accounting Files', color: 'text-purple-600' },
    { icon: FileText, label: 'Invoices', color: 'text-emerald-600' },
    { icon: FileText, label: 'Spreadsheets', color: 'text-amber-600' },
    { icon: FileText, label: 'Cashflow Statements', color: 'text-cyan-600' },
  ]

  return (
    <div className="p-4 space-y-3">
      <div className="text-sm font-semibold text-slate-700">Financial Records</div>
      <div className="space-y-2">
        {records.map((record, i) => (
          <div key={i} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-slate-50 transition-colors">
            <div className={`w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center ${record.color}`}>
              <record.icon className="w-4 h-4" />
            </div>
            <span className="text-xs font-medium text-slate-700">{record.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
