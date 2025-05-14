#include <QApplication>
#include <QPushButton>
#include <QVBoxLayout>
#include <QFormLayout>
#include <QLineEdit>
#include <QFileDialog>
#include <QFile>
#include <QTextStream>
#include <QDateTime>
#include <QMessageBox>
#include <QWidget>
#include <poppler-qt5.h>

void appendToCSV(const QString &filename, const QStringList &data) {
    QFile file(filename);
    bool newFile = !file.exists();
    if (file.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&file);
        if (newFile) {
            out << "Name,Lunch Start,Lunch End,Tea Start,Tea End,Date\n";
        }
        out << data.join(",") << "\n";
        file.close();
    }
}

void appendNote(const QString &note) {
    QFile file("notes.csv");
    if (file.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream out(&file);
        out << QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm") << "," << note << "\n";
        file.close();
    }
}

void importPDF(QWidget *parent) {
    QString path = QFileDialog::getOpenFileName(parent, "Select PDF", "", "*.pdf");
    if (path.isEmpty()) return;

    Poppler::Document *doc = Poppler::Document::load(path);
    if (!doc) {
        QMessageBox::warning(parent, "PDF Error", "Could not open PDF.");
        return;
    }

    for (int i = 0; i < doc->numPages(); ++i) {
        Poppler::Page *page = doc->page(i);
        if (!page) continue;

        QString text = page->text();
        delete page;

        QStringList lines = text.split("\n", Qt::SkipEmptyParts);
        for (const QString &line : lines) {
            if (line.contains("Lunch", Qt::CaseInsensitive) || line.contains("Tea", Qt::CaseInsensitive)) {
                QStringList parts = line.split(QRegExp("\s+"));
                if (parts.size() >= 5) {
                    QString name = parts[0];
                    QString breakType = parts[1];
                    QString start = parts[2];
                    QString end = parts[3];
                    QString date = parts[4];
                    QStringList row;

                    if (breakType.contains("lunch", Qt::CaseInsensitive)) {
                        row << name << start << end << "" << "" << date;
                    } else {
                        row << name << "" << "" << start << end << date;
                    }

                    appendToCSV("break_schedule.csv", row);
                }
            }
        }
    }
    delete doc;
    appendNote("✔ PDF imported successfully");
    QMessageBox::information(parent, "Import Complete", "PDF data imported.");
}

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    QWidget window;
    window.setWindowTitle("Break Scheduler (C++ Qt)");

    QLineEdit *nameEdit = new QLineEdit;
    QLineEdit *lunchStartEdit = new QLineEdit;
    QLineEdit *lunchEndEdit = new QLineEdit;
    QLineEdit *teaStartEdit = new QLineEdit;
    QLineEdit *teaEndEdit = new QLineEdit;

    QFormLayout *form = new QFormLayout;
    form->addRow("Name", nameEdit);
    form->addRow("Lunch Start", lunchStartEdit);
    form->addRow("Lunch End", lunchEndEdit);
    form->addRow("Tea Start", teaStartEdit);
    form->addRow("Tea End", teaEndEdit);

    QPushButton *submit = new QPushButton("Save Entry");
    QPushButton *importBtn = new QPushButton("Import PDF");

    QObject::connect(submit, &QPushButton::clicked, [&]() {
        QString name = nameEdit->text();
        QString lunchStart = lunchStartEdit->text();
        QString lunchEnd = lunchEndEdit->text();
        QString teaStart = teaStartEdit->text();
        QString teaEnd = teaEndEdit->text();

        if (name.isEmpty() || lunchStart.isEmpty() || lunchEnd.isEmpty() ||
            teaStart.isEmpty() || teaEnd.isEmpty()) {
            QMessageBox::warning(&window, "Input Error", "Please fill in all fields.");
            return;
        }

        QStringList row = { name, lunchStart, lunchEnd, teaStart, teaEnd, QDate::currentDate().toString("yyyy-MM-dd") };
        appendToCSV("break_schedule.csv", row);
        appendNote("✔ Manual entry saved by GUI");

        QMessageBox::information(&window, "Saved", "Break data saved.");
        nameEdit->clear();
        lunchStartEdit->clear();
        lunchEndEdit->clear();
        teaStartEdit->clear();
        teaEndEdit->clear();
    });

    QObject::connect(importBtn, &QPushButton::clicked, [&]() {
        importPDF(&window);
    });

    QVBoxLayout *layout = new QVBoxLayout;
    layout->addLayout(form);
    layout->addWidget(submit);
    layout->addWidget(importBtn);
    window.setLayout(layout);
    window.show();

    return app.exec();
}