#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>
#include <regex>
#include <algorithm>

/* ========= RULES & MODES ========= */

constexpr double MAX_LEGAL_WIND = 2.0;

enum class EngineMode {
    OFFICIAL,   // Enforce World Athletics wind rules
    RESEARCH    // Physics-only, allow everything
};

// 🔁 CHANGE THIS IF NEEDED
constexpr EngineMode ENGINE_MODE = EngineMode::OFFICIAL;

inline bool isWindLegal(double wind) {
    return wind <= MAX_LEGAL_WIND;
}

/* ========= DATA STRUCTURES ========= */

struct Athlete {
    std::string games, event, name, raceGroup, surface;
    double totalTime, rt, wind, altitude, radius, temp, humidity;
    int lane;
    double normalized100m;

    // NEW
    bool windLegal;
};

/* ========= PHYSICS ENGINE ========= */

class PhysicsEngine {
public:
    static constexpr double RHO_STD = 1.225; 
    static constexpr double R_DRY = 287.058; 
    static constexpr double R_VAPOR = 461.495;

    static double getAirDensity(double alt, double tempC, double humPct) {
        double T_kelvin = tempC + 273.15;
        double P = 101325.0 * pow(1.0 - 2.25577e-5 * alt, 5.25588);
        double Eso = 6.1078 * exp((17.27 * tempC) / (tempC + 237.3)) * 100.0;
        double Pv = Eso * (humPct / 100.0);
        double Pd = P - Pv;
        return (Pd / (R_DRY * T_kelvin)) + (Pv / (R_VAPOR * T_kelvin));
    }

    static double getCurveFactor(double rad, double v) {
        if (rad <= 0) return 1.0;
        double centripetalAcc = (v * v) / rad;
        double humanPowerLimit = 12.0;
        return 1.0 + (centripetalAcc / humanPowerLimit) * 0.025;
    }

    static double calculateUltimateNormalization(Athlete& a) {
        double distance = (a.event == "100m") ? 100.0 :
                          (a.event == "200m") ? 200.0 : 400.0;

        double t_move = a.totalTime - a.rt;
        double v_raw = distance / t_move;

        double rho = getAirDensity(a.altitude, a.temp, a.humidity);
        double dragCorrection = rho / RHO_STD;
        double v_wind_adj = v_raw - (a.wind * 0.05 * dragCorrection);

        double curveTax = getCurveFactor(a.radius, v_wind_adj);
        double v_geom_adj = v_wind_adj * curveTax;

        double surfaceBonus = (a.surface.find("Mondo") != std::string::npos) ? 1.0 : 0.985;
        double v_final = v_geom_adj / surfaceBonus;

        double efficiency = 1.0;
        if (a.event == "200m") efficiency = 0.988;
        if (a.event == "400m") efficiency = 0.915;

        return (100.0 / (v_final * efficiency)) + 0.100;
    }
};

/* ========= MAIN ========= */

int main() {
    std::ifstream file("Raw_Data.csv");
    std::string line, header;
    std::vector<Athlete> athletes;

    std::getline(file, header);

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string f[13];
        for(int i=0; i<13; ++i) std::getline(ss, f[i], ',');

        if (f[0].empty()) continue;

        Athlete a;
        a.games = f[0];
        a.event = f[1];
        a.name = f[2];
        a.raceGroup = f[3];
        a.totalTime = std::stod(f[4]);
        a.rt = std::stod(f[5]);
        a.lane = std::stoi(f[7]);
        a.radius = (f[8] == "Straight") ? 0 : std::stod(f[8]);
        a.wind = std::stod(f[9]);
        a.altitude = std::stod(f[10]);

        // NEW
        a.windLegal = isWindLegal(a.wind);

        std::regex rgx("(\\d+).* (\\d+)%");
        std::smatch match;
        if (std::regex_search(f[11], match, rgx)) {
            a.temp = std::stod(match.str(1));
            a.humidity = std::stod(match.str(2));
        }

        a.surface = f[12];
        a.normalized100m = PhysicsEngine::calculateUltimateNormalization(a);
        athletes.push_back(a);
    }

    /* ========= SORTING ========= */

    std::sort(athletes.begin(), athletes.end(),
        [](const Athlete& a, const Athlete& b) {
            if (ENGINE_MODE == EngineMode::OFFICIAL) {
                if (a.windLegal != b.windLegal)
                    return a.windLegal > b.windLegal;
            }
            return a.normalized100m < b.normalized100m;
        });

    /* ========= OUTPUT ========= */

    std::cout << std::left
              << std::setw(15) << "ATHLETE"
              << std::setw(8)  << "EVENT"
              << std::setw(10) << "RAW"
              << std::setw(8)  << "WIND"
              << "NORMALIZED\n";
    std::cout << std::string(70, '=') << "\n";

    for (const auto& a : athletes) {
        std::cout << std::left
                  << std::setw(15) << a.name
                  << std::setw(8)  << a.event
                  << std::setw(10) << a.totalTime
                  << std::setw(8)  << a.wind
                  << std::fixed << std::setprecision(4)
                  << a.normalized100m;

        if (!a.windLegal)
            std::cout << "  *ILLEGAL";

        std::cout << "\n";
    }

    /* ========= CSV EXPORT ========= */

    std::ofstream outFile("Olympics_Data_Normalization.csv");
    outFile << "Name,Event,RawTime,ReactionTime,Wind,Altitude,WindLegal,Normalized100m\n";

    for (const auto& a : athletes) {
        outFile << a.name << ","
                << a.event << ","
                << a.totalTime << ","
                << a.rt << ","
                << a.wind << ","
                << a.altitude << ","
                << (a.windLegal ? "YES" : "NO") << ","
                << std::fixed << std::setprecision(4)
                << a.normalized100m << "\n";
    }

    outFile.close();
    std::cout << "\nExported: Olympics_Data_Normalization.csv\n";

    return 0;
}
