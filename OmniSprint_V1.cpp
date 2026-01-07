#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cmath>
#include <iomanip>
#include <regex>
#include <algorithm>

struct Athlete {
    std::string games, event, name, raceGroup, surface;
    double totalTime, rt, wind, altitude, radius, temp, humidity;
    int lane;
    double normalized100m;
};

class PhysicsEngine {
public:
    // Constants for standard normalization (Sea Level, 15°C, 0% Humidity)
    static constexpr double RHO_STD = 1.225; 
    static constexpr double R_DRY = 287.058; 
    static constexpr double R_VAPOR = 461.495;

    // 1. Calculate precise air density (kg/m^3) using Altitude, Temp, and Humidity
    static double getAirDensity(double alt, double tempC, double humPct) {
        double T_kelvin = tempC + 273.15;
        // Pressure at altitude (Pa)
        double P = 101325.0 * pow(1.0 - 2.25577e-5 * alt, 5.25588);
        // Saturation vapor pressure (Tetens)
        double Eso = 6.1078 * exp((17.27 * tempC) / (tempC + 237.3)) * 100.0;
        double Pv = Eso * (humPct / 100.0); // Partial pressure of water vapor
        double Pd = P - Pv;                 // Partial pressure of dry air
        
        return (Pd / (R_DRY * T_kelvin)) + (Pv / (R_VAPOR * T_kelvin));
    }

    // 2. Calculate the "Curve Tax" (Force lost to centripetal acceleration)
    static double getCurveFactor(double rad, double v) {
        if (rad <= 0) return 1.0; 
        // Force Vectoring: Forward Speed is lost to stay on the curve
        // Tax is proportional to v^2 / radius
        double centripetalAcc = (v * v) / rad;
        double humanPowerLimit = 12.0; // Max acceleration capacity (m/s^2)
        return 1.0 + (centripetalAcc / humanPowerLimit) * 0.025; 
    }

    static double calculateUltimateNormalization(Athlete& a) {
        double distance = (a.event == "100m") ? 100.0 : (a.event == "200m" ? 200.0 : 400.0);
        double t_move = a.totalTime - a.rt; // Effective running time
        double v_raw = distance / t_move;

        // --- Step A: Environmental Drag Adjustment ---
        double rho = getAirDensity(a.altitude, a.temp, a.humidity);
        double dragCorrection = rho / RHO_STD;
        // Mureika Model: v_adj accounts for wind and air density
        double v_wind_adj = v_raw - (a.wind * 0.05 * dragCorrection);

        // --- Step B: Lane/Curve Geometry Adjustment ---
        double curveTax = getCurveFactor(a.radius, v_wind_adj);
        double v_geom_adj = v_wind_adj * curveTax;

        // --- Step C: Surface Energy Return ---
        // Mondo Ellipse is the benchmark; older tracks have a 1-1.5% penalty
        double surfaceBonus = (a.surface.find("Mondo") != std::string::npos) ? 1.0 : 0.985;
        double v_final = v_geom_adj / surfaceBonus;

        // --- Step D: Fatigue Scaling (Convert to 100m equivalent) ---
        // Normalizing 200m/400m back to 100m using efficiency decay constants
        double efficiency = 1.0;
        if (a.event == "200m") efficiency = 0.988; // Humans are ~1.2% slower over 200m
        if (a.event == "400m") efficiency = 0.915; // Significant drop-off for 400m

        double normalizedTime = (100.0 / (v_final * efficiency)) + 0.100;
        return normalizedTime;
    }
};

int main() {
    std::ifstream file("Raw_Data.csv");
    std::string line, header;
    std::vector<Athlete> athletes;

    std::getline(file, header); // Skip headers

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string f[13];
        for(int i=0; i<13; ++i) std::getline(ss, f[i], ',');

        if (f[0].empty()) continue;

        Athlete a;
        a.games = f[0]; a.event = f[1]; a.name = f[2]; a.raceGroup = f[3];
        a.totalTime = std::stod(f[4]);
        a.rt = std::stod(f[5]);
        a.lane = std::stoi(f[7]);
        a.radius = (f[8] == "Straight") ? 0 : std::stod(f[8]);
        a.wind = std::stod(f[9]);
        a.altitude = std::stod(f[10]);

        // Regex to parse "21°C / 58%"
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

    // Sort by the best normalized performance
    std::sort(athletes.begin(), athletes.end(), [](const Athlete& a, const Athlete& b) {
        return a.normalized100m < b.normalized100m;
    });

    std::cout << std::left << std::setw(15) << "ATHLETE" << std::setw(10) << "EVENT" 
              << std::setw(12) << "RAW TIME" << "NORMALIZED 100m (PHYSICS EQUIVALENT)\n";
    std::cout << std::string(80, '=') << "\n";

    for (const auto& a : athletes) {
        std::cout << std::left << std::setw(15) << a.name << std::setw(10) << a.event 
                  << std::setw(12) << a.totalTime << std::fixed << std::setprecision(4) 
                  << a.normalized100m << "s\n";
    }

    // --- EXPORT TO CSV ---
std::ofstream outFile("Olympics_Data_Normaliziation.csv");
outFile << "Name,Event,RawTime,ReactionTime,Wind,Altitude,Normalized100m\n";

for (const auto& a : athletes) {
    outFile << a.name << "," 
            << a.event << "," 
            << a.totalTime << "," 
            << a.rt << "," 
            << a.wind << "," 
            << a.altitude << "," 
            << std::fixed << std::setprecision(4) << a.normalized100m << "\n";
}
outFile.close();
std::cout << "\nFile 'Olympics_Data_Normaliziation.csv' exported successfully.\n";

    return 0;
}