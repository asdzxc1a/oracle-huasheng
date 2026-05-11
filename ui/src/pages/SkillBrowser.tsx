import { useState } from "react";
import { useSkills } from "../hooks/useSkills";
import { fetchSkillBody } from "../hooks/useSkills";
import ReactMarkdown from "react-markdown";

export function SkillBrowser() {
  const { skills, loading, error } = useSkills();
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [skillBody, setSkillBody] = useState<string>("");
  const [skillLoading, setSkillLoading] = useState(false);

  const handleSelect = async (name: string) => {
    setSelectedSkill(name);
    setSkillLoading(true);
    try {
      const data = await fetchSkillBody(name);
      setSkillBody(data.body);
    } catch (e) {
      setSkillBody(`Error loading skill: ${e}`);
    } finally {
      setSkillLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-parchment/60">Loading skills...</div>;
  if (error) return <div className="p-8 text-rose-400">Error: {error}</div>;

  return (
    <div className="h-full flex">
      {/* Skill list */}
      <div className="w-80 border-r border-parchment/10 overflow-y-auto p-4">
        <h2 className="text-lg font-semibold text-parchment mb-4">Skills</h2>
        <div className="space-y-2">
          {skills.map((skill) => (
            <button
              key={skill.name}
              onClick={() => handleSelect(skill.name)}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                selectedSkill === skill.name
                  ? "bg-parchment/10 border-parchment/30"
                  : "bg-transparent border-parchment/10 hover:bg-parchment/5"
              }`}
            >
              <div className="font-medium text-parchment text-sm">{skill.name}</div>
              <div className="text-xs text-parchment/50 mt-1 line-clamp-2">{skill.description}</div>
              <div className="flex gap-2 mt-2">
                {skill.has_scripts && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400">scripts</span>
                )}
                {skill.has_references && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400">refs</span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Skill body */}
      <div className="flex-1 overflow-y-auto p-8">
        {selectedSkill ? (
          <div>
            <h1 className="text-2xl font-bold text-parchment mb-6">{selectedSkill}</h1>
            {skillLoading ? (
              <div className="text-parchment/60">Loading...</div>
            ) : (
              <div className="prose prose-invert max-w-none">
                <ReactMarkdown>{skillBody}</ReactMarkdown>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-parchment/40">
            Select a skill to view its documentation
          </div>
        )}
      </div>
    </div>
  );
}
