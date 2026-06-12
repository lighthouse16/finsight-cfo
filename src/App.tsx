import AppRouter from './routes/AppRouter'
import GlobalRuntimeWarning from './components/platform/GlobalRuntimeWarning'

function App() {
  return (
    <>
      <GlobalRuntimeWarning />
      <AppRouter />
    </>
  )
}

export default App
