using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;

internal static class Launcher {
    private static string Quote(string value) {
        var result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char character in value) {
            if (character == '\\') { slashes++; continue; }
            if (character == '"') result.Append('\\', slashes * 2 + 1);
            else result.Append('\\', slashes);
            result.Append(character); slashes = 0;
        }
        result.Append('\\', slashes * 2); result.Append('"');
        return result.ToString();
    }
    [STAThread]
    private static int Main(string[] args) {
        try {
            string root = AppDomain.CurrentDomain.BaseDirectory;
            var arguments = new StringBuilder("-B -m telazocraft");
            foreach (string arg in args) arguments.Append(" " + Quote(arg));
            var start = new ProcessStartInfo(Path.Combine(root, "python", "pythonw.exe"), arguments.ToString());
            start.WorkingDirectory = root; start.UseShellExecute = false; start.CreateNoWindow = true;
            using (var child = Process.Start(start)) { child.WaitForExit(); return child.ExitCode; }
        } catch (Exception error) {
            MessageBox.Show("No se pudo abrir Telazocraft: " + error.Message, "Telazocraft", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
