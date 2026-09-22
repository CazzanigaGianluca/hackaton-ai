import FileUpload from "@/components/FileUpload";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 bg-gray-50 px-4 py-16">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-bold text-gray-900">
          Dove vanno i tuoi soldi ogni mese?
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          Carica il tuo Estratto Conto (CSV o PDF): analizziamo le tue spese, le confrontiamo
          con la media delle famiglie italiane (dati ISTAT) e ti aiutiamo a capire dove vanno i
          soldi — senza consigli di investimento, solo educazione finanziaria.
        </p>
      </div>
      <FileUpload />
    </main>
  );
}
