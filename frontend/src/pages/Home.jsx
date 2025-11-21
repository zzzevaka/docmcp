import MainLayout from '../components/layout/MainLayout'

function Home() {
  return (
    <MainLayout>
      <div className="px-4 py-6">
        <div className="text-center py-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome to DocMCP
          </h1>
          <p className="text-gray-600">
            Your documentation workspace is ready
          </p>
        </div>
      </div>
    </MainLayout>
  )
}

export default Home
